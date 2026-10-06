// Render prototype/corison-100ka.html to an MP4, frame by frame (deterministic, any speed of machine).
// Usage: node scripts/render_corison_video.mjs [out.mp4] [fps] [width] [height]
// Needs Playwright (Chromium) and ffmpeg. Serves prototype/ on a local port.
import { createRequire } from "node:module";
import http from "node:http"; import fs from "node:fs"; import path from "node:path"; import { execFileSync } from "node:child_process";
import os from "node:os";
const { chromium } = createRequire(import.meta.url)("playwright");   // CommonJS lookup also finds a global install via NODE_PATH
const [out = "corison-100ka.mp4", fps = "30", W = "1280", H = "720", only = ""] = process.argv.slice(2);
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "../prototype");
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".jpg": "image/jpeg", ".png": "image/png" };
const srv = http.createServer((q, r) => { const p = path.join(root, decodeURIComponent(q.url.split("?")[0]));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { "content-type": types[path.extname(p)] || "application/octet-stream" }); fs.createReadStream(p).pipe(r); });
await new Promise(ok => srv.listen(0, ok));
const port = srv.address().port, dir = fs.mkdtempSync(path.join(os.tmpdir(), "c100-"));
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: +W, height: +H } });
const errs = []; page.on("pageerror", e => errs.push(String(e))); page.on("console", m => m.type() === "error" && errs.push(m.text()));
await page.goto(`http://localhost:${port}/corison-100ka.html?play=0`);
await page.waitForFunction(() => window.C100 && window.C100.ready, null, { timeout: 120000 });
const dur = await page.evaluate(() => window.C100.DUR);
const times = only ? only.split(",").map(Number) : Array.from({ length: Math.round(dur * fps) }, (_, k) => k / fps);
const t0 = Date.now();
for (let k = 0; k < times.length; k++) {
  await page.evaluate(s => window.C100.frame(s), times[k]);
  await page.screenshot({ path: path.join(dir, `f${String(k).padStart(5, "0")}.png`) });
  if (k % 60 === 0) console.log(`frame ${k}/${times.length}  ${((Date.now() - t0) / 1000).toFixed(0)} s`);
}
await browser.close(); srv.close();
if (errs.length) console.log("page errors:", errs.slice(0, 5));
if (only) { console.log("stills in", dir); process.exit(0); }
execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", fps, "-i", path.join(dir, "f%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
  "-crf", "20", "-preset", "slow", "-movflags", "+faststart", out], { stdio: "inherit" });
fs.rmSync(dir, { recursive: true });
console.log("wrote", out);
