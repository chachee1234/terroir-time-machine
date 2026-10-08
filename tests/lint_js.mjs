// Syntax check for every inline <script> in prototype/**/*.html and every .mjs in the repo
// (classic scripts as CommonJS, type="module" as ES modules), using `node --check`.
//   node tests/lint_js.mjs
import { readFileSync, readdirSync, writeFileSync, mkdtempSync, rmSync, statSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const walk = d => readdirSync(d).flatMap(n => {
  const p = path.join(d, n);
  if (n === "node_modules" || n.startsWith(".")) return [];
  return statSync(p).isDirectory() ? walk(p) : [p];
});

const tmp = mkdtempSync(path.join(tmpdir(), "ttm-lint-"));
const failures = [];
let checked = 0;
function check(file, label) {
  checked++;
  try { execFileSync(process.execPath, ["--check", file], { stdio: "pipe" }); }
  catch (e) { failures.push(`${label}\n${String(e.stderr).split("\n").slice(0, 6).join("\n")}`); }
}

for (const page of walk(path.join(ROOT, "prototype")).filter(p => p.endsWith(".html"))) {
  const html = readFileSync(page, "utf8"), rel = path.relative(ROOT, page);
  const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/g;
  let m, n = 0;
  while ((m = re.exec(html))) {
    const attrs = m[1], body = m[2];
    if (/\bsrc=/.test(attrs) || /type="(importmap|text\/x-[^"]*|application\/json)"/.test(attrs) || !body.trim()) continue;
    const line = html.slice(0, m.index).split("\n").length;
    const file = path.join(tmp, `${path.basename(page, ".html")}-${n++}.${/type="module"/.test(attrs) ? "mjs" : "cjs"}`);
    writeFileSync(file, "\n".repeat(line - 1) + body);    // keep line numbers aligned with the page
    check(file, `${rel}: <script> at line ${line}`);
  }
}
for (const f of walk(ROOT).filter(p => p.endsWith(".mjs"))) check(f, path.relative(ROOT, f));
rmSync(tmp, { recursive: true, force: true });

if (failures.length) { console.error(failures.join("\n\n")); console.error(`FAIL: ${failures.length} of ${checked} scripts`); process.exit(1); }
console.log(`PASS: ${checked} scripts parse`);
