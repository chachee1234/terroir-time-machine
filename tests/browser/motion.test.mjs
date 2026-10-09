// Plate motion and mountain building: the deep-time globe shows plate outlines with streaks that keep
// moving, and the block's section panel has a mountain-building view that opens on its chapters.
// Run: node --test "tests/browser/*.test.mjs"
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { serve, launch, open, problems } from "./harness.mjs";

let srv, browser;
before(async () => { srv = await serve(); browser = await launch(); });
after(async () => { await browser?.close(); srv?.server.close(); });

const TM = "/prototype/timemachine.html?debug";
const frames = (page, n) => page.evaluate(n => new Promise(ok => { const f = () => --n > 0 ? requestAnimationFrame(f) : ok(); requestAnimationFrame(f); }), n);
// share of the canvas's pixels that are drawn (not transparent)
const inked = (page, id) => page.$eval(id, c => { const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data;
  let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++; return n / (d.length / 4); });

test("deep time: plate outlines are on and the motion streaks move while paused", async () => {
  const { page, context, log } = await open(browser, srv.base + TM + "&t=200");
  await page.waitForFunction(() => TTM.PM.ok && TTM.MV.pts.geometry.drawRange.count > 0, null, { timeout: 120000 });
  const pressed = await page.getAttribute("#play", "aria-pressed");
  const on = await page.evaluate(() => [TTM.gUni.uPlOn.value, TTM.MV.pts.visible, TTM.MV.seeds.length]);
  const head = () => page.evaluate(() => { const a = TTM.MV.al, p = TTM.MV.pos; let i = 0; while (i < a.length && a[i] < 0.3) i++; return [i, p[3 * i], p[3 * i + 1], p[3 * i + 2]]; });
  const [i0] = await head(); const p0 = await page.evaluate(i => Array.from(TTM.MV.pos.slice(3 * i, 3 * i + 3)), i0);
  await frames(page, 20);
  const p1 = await page.evaluate(i => Array.from(TTM.MV.pos.slice(3 * i, 3 * i + 3)), i0);
  const legend = await page.isHidden("#lgMove");
  await context.close();
  assert.equal(pressed, "false");
  assert.equal(on[0], 1); assert.equal(on[1], true); assert.ok(on[2] > 50, `${on[2]} seeds`);
  assert.ok(Math.hypot(p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]) > 1e-4, "streak did not move");
  assert.ok(p1.every(Number.isFinite));
  assert.equal(legend, false);
  assert.deepEqual(problems(log), []);
});

test("on the block the plate streaks are off", async () => {
  const { page, context, log } = await open(browser, srv.base + TM + "&t=5");
  await frames(page, 3);
  const on = await page.evaluate(() => [TTM.gUni.uPlOn.value, TTM.MV.pts.visible]);
  await context.close();
  assert.deepEqual(on, [0, false]);
  assert.deepEqual(problems(log), []);
});

test("mountain-building section: drawn, labelled schematic, and switchable with the plate view", async () => {
  const { page, context, log } = await open(browser, srv.base + TM + "&t=2");
  await page.evaluate(() => document.getElementById("sdBtn").click());
  await frames(page, 3);
  const head = await page.textContent("#sdHead"), note = await page.textContent("#sdNote"), ink = await inked(page, "#sdCv");
  await page.evaluate(() => document.getElementById("sdMode").click());
  await frames(page, 3);
  const head2 = await page.textContent("#sdHead");
  await context.close();
  assert.match(head, /Mountain building/);
  assert.match(note, /Illustrative process · geometry and timing are schematic/);
  assert.ok(ink > 0.4, `only ${(ink * 100).toFixed(0)}% of the section is drawn`);
  assert.match(head2, /Plates in motion/);
  assert.deepEqual(problems(log), []);
});

test("before the volcanoes the panel opens on the plate view", async () => {
  const { page, context, log } = await open(browser, srv.base + TM + "&t=20");
  await page.evaluate(() => document.getElementById("sdBtn").click());
  await frames(page, 3);
  const head = await page.textContent("#sdHead");
  await context.close();
  assert.match(head, /Plates in motion/);
  assert.deepEqual(problems(log), []);
});

test("reaching a mountain-building chapter opens the section by itself", { timeout: 300000 }, async () => {
  const { page, context, log } = await open(browser, srv.base + TM + "&t=9");
  const before = await page.isHidden("#sub");
  await page.click("#next");
  await page.waitForFunction(() => !document.getElementById("sub").hidden, null, { timeout: 180000 });
  const head = await page.textContent("#sdHead");
  await context.close();
  assert.equal(before, true);
  assert.match(head, /Mountain building/);
  assert.deepEqual(problems(log), []);
});
