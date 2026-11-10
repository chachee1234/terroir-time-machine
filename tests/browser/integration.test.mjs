// Integration: the pipeline that turns repo data into what reviewers open. scripts/build_share.py
// bundles the viewer and every data file into one HTML page; that page must then run from a bare
// file:// path with no repo next to it, fetch nothing from disk, and keep the feedback panel working.
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { ROOT, launch, open, problems } from "./harness.mjs";

let browser, dir;
before(async () => { browser = await launch(); dir = mkdtempSync(path.join(tmpdir(), "ttm-share-")); });
after(async () => { await browser?.close(); rmSync(dir, { recursive: true, force: true }); });

function build(args, name) {
  const out = path.join(dir, name);
  execFileSync("python3", [path.join(ROOT, "scripts/build_share.py"), ...args, "--out", out], { cwd: ROOT, stdio: "pipe", timeout: 600000 });
  assert.ok(statSync(out).size > 100000, `${name} was written`);
  return pathToFileURL(out).href;
}

for (const [label, args, name] of [["Napa time machine (lite)", ["--lite"], "lite.html"], ["Gibraltar", ["--page", "gibraltar"], "gib.html"]]) {
  test(`share build runs offline from a single file: ${label}`, { timeout: 900000 }, async () => {
    const url = build(args, name);
    const { page, context, log } = await open(browser, url, { settle: 4000, viewport: { width: 800, height: 600 } });
    const title = await page.title();
    const card = await page.textContent("#cTitle");
    // the review copy's feedback panel opens and records a note with its context
    await page.click("#fbBtn");
    await page.fill("#fbText", "integration test note");
    await page.click("#fbAdd");
    const notes = await page.$$eval("#fbList li", li => li.map(e => e.textContent));
    await context.close();
    assert.match(title, /\(review copy\)/);
    assert.ok(card && !/Could not load/.test(card), `chapter card: ${card}`);
    assert.equal(notes.length, 1);
    assert.match(notes[0], /integration test note/);
    assert.deepEqual(problems(log), [], "no uncaught errors, no files missing, no unlisted hosts");
  });
}
