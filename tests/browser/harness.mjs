// Shared harness for the browser tests (node:test + Playwright, Chromium headless).
//
// Serves the repo root on 127.0.0.1 so pages load exactly as they do from GitHub Pages
// (prototype/timemachine.html fetches ../SCENES.json and ../data/...). External hosts are never
// contacted: three.js r128 is answered from a local copy (THREE_DIR, a checkout of three.js tag
// r128, see tests/README.md), fonts are aborted, and any other host is recorded as a violation.
import { createServer } from "node:http";
import { createReadStream, existsSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { execSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

function loadPlaywright() {
  const require = createRequire(import.meta.url);
  try { return require("playwright"); } catch { /* fall back to a global install */ }
  const root = execSync("npm root -g", { encoding: "utf8" }).trim();
  return require(path.join(root, "playwright"));
}
export const { chromium } = loadPlaywright();

const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript",
  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg", ".mp4": "video/mp4",
  ".bin": "application/octet-stream", ".u8": "application/octet-stream", ".css": "text/css" };

// Static server rooted at `root`; refuses anything that resolves outside it.
export function serve(root = ROOT) {
  const server = createServer((req, res) => {
    let rel;
    try { rel = decodeURIComponent(new URL(req.url, "http://x").pathname); } catch { res.writeHead(400); return res.end(); }
    const file = path.join(root, rel);
    if (!file.startsWith(root + path.sep) || !existsSync(file) || statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "content-type": MIME[path.extname(file)] || "application/octet-stream" });
    createReadStream(file).pipe(res);
  });
  return new Promise(ok => server.listen(0, "127.0.0.1", () => ok({ server, base: `http://127.0.0.1:${server.address().port}` })));
}

// Hosts the pages may name. Everything else is a privacy/tracking violation (ACCEPTANCE_TESTS Q04).
export const ALLOWED_HOSTS = ["cdnjs.cloudflare.com", "cdn.jsdelivr.net", "fonts.googleapis.com", "fonts.gstatic.com"];
// Same-origin files the viewer may ask for that are allowed to be missing. Empty: optional data (the
// daily weather) is only requested when assets/regions/index.json lists it, so any 404 is a real fault.
export const OPTIONAL = [];

const THREE_DIR = process.env.THREE_DIR || path.join(ROOT, "..", "three-r128");
const THREE_FILES = {
  "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js": "build/three.min.js",
  "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js": "examples/js/controls/OrbitControls.js",
};
if (!existsSync(path.join(THREE_DIR, THREE_FILES[Object.keys(THREE_FILES)[0]])))
  throw new Error(`three.js r128 not found in ${THREE_DIR}; set THREE_DIR (see tests/README.md)`);

export async function launch(extraArgs = []) {
  return chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", ...extraArgs] });
}

// Opens `url` and records everything a test needs to judge the load.
export async function open(browser, url, { viewport = { width: 1440, height: 900 }, reducedMotion, settle = 2500 } = {}) {
  const context = await browser.newContext({ viewport, reducedMotion });
  const page = await context.newPage();
  const log = { pageErrors: [], consoleErrors: [], missing: [], foreign: [], dialogs: [] };
  page.on("pageerror", e => log.pageErrors.push(e.message));
  page.on("dialog", d => { log.dialogs.push(d.message()); d.dismiss().catch(() => {}); });
  page.on("console", m => { if (m.type() === "error") log.consoleErrors.push({ text: m.text(), url: m.location().url }); });
  page.on("response", r => { if (r.status() >= 400) log.missing.push(r.url()); });
  page.on("requestfailed", r => { const u = r.url(); if (u.startsWith("http://127.0.0.1") || u.startsWith("file:")) log.missing.push(u); });
  await context.route(/^https?:\/\//, route => {
    const u = route.request().url(), host = new URL(u).hostname;
    if (host === "127.0.0.1") return route.continue();
    const local = THREE_FILES[u.split("?")[0]];
    if (local) return route.fulfill({ path: path.join(THREE_DIR, local), contentType: "text/javascript",
      headers: { "access-control-allow-origin": "*" } });
    if (!ALLOWED_HOSTS.includes(host)) log.foreign.push(u);
    return route.abort("blockedbyclient");
  });
  await page.goto(url, { waitUntil: "load", timeout: 120000 });
  if (settle) await page.waitForTimeout(settle);
  return { page, context, log };
}

const optional = u => OPTIONAL.some(re => re.test(u));
// Problems with a load: uncaught errors, console errors that are not the expected optional/blocked
// fetches, missing same-origin files, requests to unlisted hosts.
export function problems(log) {
  const out = [];
  log.pageErrors.forEach(e => out.push("uncaught: " + e));
  log.foreign.forEach(u => out.push("request to unlisted host: " + u));
  log.missing.filter(u => !optional(u)).forEach(u => out.push("missing file: " + u));
  // "Failed to load resource" lines repeat what `missing` and `foreign` already judge
  log.consoleErrors.filter(c => !/^Failed to load resource/.test(c.text))
    .forEach(c => out.push("console error: " + c.text + (c.url ? " (" + c.url + ")" : "")));
  return out;
}
