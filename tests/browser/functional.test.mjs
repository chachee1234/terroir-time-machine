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

test("the site root (index.html) forwards to the time machine", async () => {
  const { page, context, log } = await open(browser, srv.base + "/index.html", { settle: 1500 });
  const u = new URL(page.url());
  await context.close();
  assert.equal(u.pathname, TM);
  assert.deepEqual(problems(log), []);
});

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

test("Soils chip drapes the soil survey, and the section column shows the surveyed map unit with a fallback outside it", { timeout: 300000 }, async () => {
  const { page, context, log } = await open(browser, srv.base + `${TM}?t=0&debug`, { settle: 6000 });
  await page.waitForFunction(() => window.TTM && TTM.SOIL.ok, null, { timeout: 120000 });
  assert.equal(await page.isVisible("#soilBtn"), true);
  await page.click("#geoBtn"); await page.click("#soilBtn");          // one map at a time
  assert.equal(await page.getAttribute("#soilBtn", "aria-pressed"), "true");
  assert.equal(await page.getAttribute("#geoBtn", "aria-pressed"), "false");
  await page.waitForFunction(() => !document.getElementById("lgSoil").hidden, null, { timeout: 60000 });
  assert.match(await page.textContent("#soilSw"), /Bressa/);
  // Corison winery (38.484983, -122.44736): SSURGO map unit 170, Pleasanton loam
  await page.evaluate(() => TTM.xsSet(16.307, 20.358));
  await page.click("#xsBtn");
  await page.waitForFunction(() => /Pleasanton loam/.test(document.getElementById("xsNote").textContent), null, { timeout: 60000 });
  const note = await page.textContent("#xsNote");
  assert.match(note, /^USDA SSURGO 1:24,000, map unit average, not a pit at this spot\./);
  assert.match(note, /SIM 2956 unit Qf/);
  // east of the Napa and Sonoma surveys: the schematic column, saying why
  await page.evaluate(() => TTM.xsSet(38, -6));
  await page.waitForFunction(() => /^Schematic column/.test(document.getElementById("xsNote").textContent), null, { timeout: 60000 });
  await context.close();
  assert.deepEqual(problems(log), []);
});

test("How it formed: the tour steps through the region's chapters and ends on the soil summary", { timeout: 600000 }, async () => {
  const { page, context, log } = await open(browser, srv.base + `${TM}?t=0&debug`, { viewport: { width: 900, height: 600 }, settle: 6000 });
  await page.waitForFunction(() => window.TTM && TTM.SOIL.ok, null, { timeout: 180000 });
  assert.equal(await page.isHidden("#story"), true);
  await page.click("#stBtn");
  assert.equal(await page.getAttribute("#stBtn", "aria-pressed"), "true");
  assert.deepEqual(await page.$$eval("#stDots button", bs => bs.map(b => b.textContent)),
    ["Subduction", "Seafloor", "Faults", "Volcanoes", "Volcano", "Caldera", "Valleys", "Soils"]);
  assert.equal(await page.textContent("#stN"), "Step 8 of 8");
  // the last step: soil map coloured by texture, shares that add up, and the survey's own soil names
  await page.waitForFunction(() => !document.getElementById("stSoil").hidden && /Bressa/.test(document.getElementById("stSoil").textContent), null, { timeout: 120000 });
  assert.equal(await page.getAttribute("#soilBtn", "aria-pressed"), "true");
  assert.equal(await page.getAttribute('#soilMode [data-m="texture"]', "aria-pressed"), "true");
  const shares = await page.evaluate(() => ({ tx: TTM.soilShares("texture"), dp: TTM.soilShares("depth"),
    all: TTM.SOIL.meta.units.reduce((a, u) => a + (u.area_pct || 0), 0) }));
  for (const k of ["tx", "dp"]) assert.ok(Math.abs(shares[k].reduce((a, b) => a + b, 0) - shares.all) < 0.01, k + " shares cover every map unit once");
  assert.match(await page.textContent("#soilLb"), /^Topsoil texture/);
  // Back leaves the soil step for the one before it; the step marker follows
  await page.click("#stPrev");
  await page.waitForFunction(() => document.querySelector('#stDots [aria-current="step"]')?.textContent === "Valleys", null, { timeout: 240000, polling: 1000 });
  assert.equal(await page.isHidden("#stSoil"), true);
  await page.click("#stX");
  assert.equal(await page.isHidden("#story"), true);
  await context.close();
  assert.deepEqual(problems(log), []);
});

// Data-driven, so it keeps holding as the autopilot fills a region's gaps and adds its soil survey.
test("How it formed: a region strikes out the steps its file lists as gaps, and says so when it has no soil survey", { timeout: 300000 }, async () => {
  const id = "northern_sonoma";
  const own = JSON.parse(readFileSync(path.join(ROOT, "data/regions", id, "scenes.json"), "utf8"));
  const layers = JSON.parse(readFileSync(path.join(ROOT, "prototype/assets/regions/index.json"), "utf8")).regions.find(r => r.id === id).layers;
  const NAME = { ch_250ma: "Subduction", ch_150ma: "Seafloor", ch_28ma: "Faults", ch_8ma: "Volcanoes", ch_3_0ma: "Volcano", ch_2_85ma: "Caldera", ch_1ma: "Valleys", today: "Soils" };
  const { page, context, log } = await open(browser, srv.base + `${TM}?region=${id}&t=0`, { viewport: { width: 900, height: 600 }, settle: 6000 });
  await page.waitForFunction(() => document.querySelectorAll("#stDots button").length > 2, null, { timeout: 120000 });
  await page.click("#stBtn");
  const steps = await page.$$eval("#stDots button", bs => bs.map(b => ({ t: b.textContent, off: b.disabled, why: b.title })));
  for (const g of (own.gaps || []).filter(g => NAME[g.id])) {
    const st = steps.find(s => s.t === NAME[g.id]);
    assert.ok(st && st.off, `${g.id} is listed as a gap, so its step is struck out`);
    assert.equal(st.why, "Not yet written for this region: " + g.reason);
  }
  assert.equal(steps.find(s => s.t === "Soils").off, false);
  await page.waitForFunction(() => !document.getElementById("stSoil").hidden, null, { timeout: 120000 });
  if (!layers.includes("soils")) assert.match(await page.textContent("#stSoil"), /not loaded for this region yet/);
  await context.close();
  assert.deepEqual(problems(log), []);
});
