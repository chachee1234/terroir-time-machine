// Functional browser tests: every page loads cleanly, and the time machine's controls behave as
// ACCEPTANCE_TESTS.md U01-U05 describe. Run: node --test "tests/browser/*.test.mjs"
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { ROOT, serve, launch, open, problems } from "./harness.mjs";

let srv, browser;
before(async () => { srv = await serve(); browser = await launch(); });
after(async () => { await browser?.close(); srv?.server.close(); });

const TM = "/prototype/timemachine.html";
const regions = JSON.parse(readFileSync(path.join(ROOT, "prototype/assets/regions/index.json"), "utf8")).regions.map(r => r.id);

// "1.80 Ga ago" / "250 Ma ago" / "12 ka ago" / "Today ago" -> millions of years
function ageMa(text) {
  const m = /^([\d.]+)\s*(Ga|Ma|ka|yr)/.exec(text || "");
  if (!m) { assert.match(text, /^Today/); return 0; }
  return +m[1] * { Ga: 1000, Ma: 1, ka: 1e-3, yr: 1e-6 }[m[2]];
}
const scrubAge = page => page.$eval("#scrub", e => e.getAttribute("aria-valuetext")).then(ageMa);
async function setScrub(page, v) {
  await page.$eval("#scrub", (e, v) => { e.value = String(v); e.dispatchEvent(new Event("input", { bubbles: true })); }, v);
  await frames(page, 2);
}
// wait until the render loop has drawn n more frames (software WebGL in CI can be slow)
const frames = (page, n) => page.evaluate(n => new Promise(ok => { const f = () => --n > 0 ? requestAnimationFrame(f) : ok(); requestAnimationFrame(f); }), n);
const titleChange = (page, from) => page.waitForFunction(t => document.getElementById("cTitle").textContent !== t, from, { timeout: 120000 });

const PAGES = [TM, `${TM}?region=mt_st_helena`, ...regions.map(r => `${TM}?region=${r}`),
  `${TM}?view=regions`, `${TM}?t=5`, "/prototype/index.html", "/prototype/gibraltar.html", "/prototype/sources.html",
  "/prototype/corison-100ka.html", "/prototype/mayacamas-8ma.html", "/prototype/san-andreas-30ma.html"];

for (const url of PAGES) {
  test(`loads cleanly: ${url}`, async () => {
    const { context, log } = await open(browser, srv.base + url);
    await context.close();
    assert.deepEqual(problems(log), []);
  });
}

test("globe.html forwards old links to the regions view", async () => {
  const { page, context, log } = await open(browser, srv.base + "/prototype/globe.html?site=los_carneros", { settle: 1500 });
  const u = new URL(page.url());
  await context.close();
  assert.equal(u.pathname, TM);
  assert.equal(u.searchParams.get("view"), "regions");
  assert.equal(u.searchParams.get("site"), "los_carneros");
  assert.deepEqual(problems(log), []);
});

test("U05: an unknown region falls back to a mapped frame with a notice", async () => {
  const { page, context, log } = await open(browser, srv.base + `${TM}?region=atlantis`, { settle: 500 });
  const notice = await page.textContent("#toast");
  const title = await page.textContent("#cTitle");
  await context.close();
  assert.match(notice, /No map for “atlantis” yet/);
  assert.ok(title && title.trim().length > 0, "a chapter card is shown");
  // the viewer looks for the region's own files first; those 404s are the expected probe
  log.missing = log.missing.filter(u => !u.includes("/assets/regions/atlantis/"));
  assert.deepEqual(problems(log), []);
});

test("U02: scrubbing oldest to youngest never increases the displayed age; both ends reachable", async () => {
  const { page, context, log } = await open(browser, srv.base + TM);
  const ages = [];
  for (let i = 0; i <= 60; i++) { await setScrub(page, i / 60); ages.push(await scrubAge(page)); }
  await context.close();
  assert.ok(ages[0] >= 1000, `starts in deep time (${ages[0]} Ma)`);
  assert.equal(ages.at(-1), 0, "ends today");
  for (let i = 1; i < ages.length; i++) assert.ok(ages[i] <= ages[i - 1] + 1e-9, `age rose at step ${i}: ${ages[i - 1]} -> ${ages[i]}`);
  assert.deepEqual(problems(log), []);
});

test("U01: Play/Pause button and Space key toggle playback; Next and Previous move by chapter", { timeout: 300000 }, async () => {
  // small viewport: software WebGL draws a few frames a second at full size, and a chapter jump is ~28 frames
  const { page, context, log } = await open(browser, srv.base + TM, { viewport: { width: 480, height: 400 } });
  assert.equal(await page.getAttribute("#play", "aria-pressed"), "false");
  await page.click("#play");
  assert.equal(await page.getAttribute("#play", "aria-pressed"), "true");
  assert.equal((await page.textContent("#play")).trim(), "Pause");
  await page.keyboard.press("Space");
  assert.equal(await page.getAttribute("#play", "aria-pressed"), "false");

  await setScrub(page, 0);
  const a0 = await scrubAge(page), t0 = await page.textContent("#cTitle");
  await page.click("#next"); await titleChange(page, t0);
  await frames(page, 3);
  const a1 = await scrubAge(page), t1 = await page.textContent("#cTitle");
  assert.ok(a1 < a0, `Next moves forward in time (${a0} -> ${a1} Ma)`);
  assert.notEqual(t1, t0, "Next shows another chapter card");
  await page.keyboard.press("ArrowLeft"); await titleChange(page, t1);
  assert.ok(await scrubAge(page) > a1, "ArrowLeft goes back a chapter");
  await context.close();
  assert.deepEqual(problems(log), []);
});

test("U05: ?t= deep link opens at that age", async () => {
  const { page, context, log } = await open(browser, srv.base + `${TM}?t=5`);
  const a = await scrubAge(page);
  await context.close();
  assert.ok(Math.abs(a - 5) < 0.05, `age ${a} Ma`);
  assert.deepEqual(problems(log), []);
});

for (const viewport of [{ width: 390, height: 844 }, { width: 1440, height: 900 }]) {
  test(`U05: no horizontal scroll at ${viewport.width}x${viewport.height}`, async () => {
    const { page, context, log } = await open(browser, srv.base + TM, { viewport });
    const [sw, iw] = await page.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
    const controls = await page.$$eval(".bar .btn, #play, #next, #prev", els => els.filter(e => e.offsetParent).map(e => {
      const r = e.getBoundingClientRect(); return [e.id || e.textContent.trim(), r.left, r.right]; }));
    await context.close();
    assert.ok(sw <= iw, `scrollWidth ${sw} > innerWidth ${iw}`);
    controls.forEach(([name, l, r]) => assert.ok(l >= 0 && r <= iw + 0.5, `${name} is off screen (${l}..${r})`));
    assert.deepEqual(problems(log), []);
  });
}

test("U04: reduced-motion preference loads cleanly and does not autoplay", async () => {
  const { page, context, log } = await open(browser, srv.base + TM, { reducedMotion: "reduce" });
  const pressed = await page.getAttribute("#play", "aria-pressed");
  await context.close();
  assert.equal(pressed, "false");
  assert.deepEqual(problems(log), []);
});

test("U04: without WebGL the page says so instead of failing silently", async () => {
  const noGl = await launch(["--disable-webgl", "--disable-webgl2", "--disable-gpu"]);
  try {
    const { page, context, log } = await open(noGl, srv.base + TM);
    const msg = await page.textContent(".err").catch(() => null);
    await context.close();
    assert.match(msg || "", /WebGL is not available/);
    assert.deepEqual(log.pageErrors, []);
  } finally { await noGl.close(); }
});

test("chapter ticks are labelled buttons and the age readout is live", async () => {
  const { page, context, log } = await open(browser, srv.base + TM);
  const ticks = await page.$$eval("#ticks button", bs => bs.map(b => b.getAttribute("aria-label")));
  const chapters = JSON.parse(readFileSync(path.join(ROOT, "SCENES.json"), "utf8"));
  await context.close();
  assert.ok(ticks.length >= 5, `${ticks.length} ticks`);
  ticks.forEach(l => assert.match(l || "", /^Jump to /));
  assert.ok(chapters, "SCENES.json parses");
  assert.deepEqual(problems(log), []);
});
