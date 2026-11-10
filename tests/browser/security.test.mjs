// Browser security pass: URL parameters are attacker-controlled (anyone can send a link), so every
// parameter a page reads is fed script-injection and junk payloads. A page passes when no payload
// runs, no markup from the URL reaches the DOM, nothing throws, and no request leaves the allowed hosts.
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { serve, launch, open, problems } from "./harness.mjs";

let srv, browser;
before(async () => { srv = await serve(); browser = await launch(); });
after(async () => { await browser?.close(); srv?.server.close(); });

const XSS = [`"><img src=x onerror="window.__xss=1">`, `javascript:window.__xss=1`, `</script><script>window.__xss=1</script>`,
  `\${window.__xss=1}`, `__proto__`];
const JUNK = ["", "NaN", "-1", "1e309", "%E0%A4%A", "a".repeat(5000)];

// page -> the query parameters (or hash) it reads
const TARGETS = [
  { page: "/prototype/timemachine.html", params: ["region", "loc", "site", "view", "glref", "t", "cam"] },
  { page: "/prototype/gibraltar.html", params: ["chapter", "t", "still"] },
  { page: "/prototype/corison-100ka.html", params: ["play", "t", "still"] },
  { page: "/prototype/mayacamas-8ma.html", params: ["play", "t"] },
  { page: "/prototype/san-andreas-30ma.html", params: ["play", "t"] },
  { page: "/prototype/globe.html", params: ["site"] },
];

async function probe(url, settle = 1500) {
  const { page, context, log } = await open(browser, url, { settle, viewport: { width: 480, height: 400 } });
  const hit = await page.evaluate(() => ({ xss: window.__xss, img: !!document.querySelector('img[src="x"]'),
    js: [...document.querySelectorAll("a[href]")].some(a => /^\s*javascript:/i.test(a.getAttribute("href"))) }));
  await context.close();
  return { hit, log };
}

for (const { page, params } of TARGETS) {
  test(`script injection through URL parameters does not run: ${page}`, { timeout: 600000 }, async () => {
    for (const payload of XSS) {
      const q = new URLSearchParams(params.map(k => [k, payload])).toString();
      const { hit, log } = await probe(`${srv.base}${page}?${q}`);
      assert.equal(hit.xss, undefined, `payload ran: ${payload}`);
      assert.equal(hit.img, false, `markup from the URL reached the page: ${payload}`);
      assert.equal(hit.js, false, `a javascript: link was built from: ${payload}`);
      assert.deepEqual(log.dialogs, []);
      assert.deepEqual(log.foreign, [], "no request to an unlisted host");
    }
  });

  test(`junk URL parameters do not crash: ${page}`, { timeout: 600000 }, async () => {
    for (const k of params) for (const v of JUNK) {
      const { log } = await probe(`${srv.base}${page}?${encodeURIComponent(k)}=${encodeURIComponent(v)}`, 1000);
      assert.deepEqual(log.pageErrors, [], `${k}=${v.slice(0, 20)}`);
    }
  });
}

test("hash-driven scene id cannot inject markup: index.html", async () => {
  for (const payload of XSS) {
    const { hit, log } = await probe(`${srv.base}/prototype/index.html#scene=${encodeURIComponent(payload)}`);
    assert.equal(hit.xss, undefined);
    assert.equal(hit.img, false);
    assert.deepEqual(problems(log), []);
  }
});

test("the static server used by these tests refuses path traversal", async () => {
  for (const p of ["/../../etc/passwd", "/%2e%2e/%2e%2e/etc/passwd", "/prototype/..%2f..%2f..%2fetc%2fpasswd"]) {
    const r = await fetch(srv.base + p);
    assert.equal(r.status, 404, p);
  }
});
