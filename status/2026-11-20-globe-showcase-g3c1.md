# 2026-11-20 · globe-showcase · G3c1 plate-motion arrows

**Step:** G3c1 (split from G3c under the owner's 2026-10-21 rule; G3c2 transform offsets is next).

**Change:** `prototype/timemachine.html`. One arrow per plate, at the plate's centre (the middle of its present-day coastlines), carried by its rotation from `muller2019.json` to the age shown. The arrow points the way the centre moves over the 1 Myr around that age, toward today. Length follows speed but is exaggerated; the legend says so. Plates that do not exist at the age get no arrow. Drawn only 0–250 Ma, with the plate-motion layer. Legend text updated.

**Checks run (commands from the repo root):**
- `node tests/lint_js.mjs`: PASS, 17 scripts parse.
- `python3 -m unittest discover -s scripts -p 'test_*.py'`: 210 tests, OK (2 skipped).
- `node --test --test-timeout=900000 tests/browser/functional.test.mjs`: 26/26 pass.
- `node --test --test-timeout=900000 tests/browser/integration.test.mjs`: 2/2 pass.
- `node --test --test-timeout=900000 tests/browser/motion.test.mjs`: 6/6 pass.
- `node --test --test-timeout=0 tests/browser/security.test.mjs`: 14/14 pass. An earlier run with a 900 s file limit stopped after 7 subtests; that was a timeout, not a failure. Rerun with no per-test limit passed all 14.
- Headless load of `timemachine.html?debug&t=200` in the test harness: no page errors. A screenshot was taken and shows arrow-like marks near Laurentia, but the arrows were not checked one by one.

**Not verified:** the arrows at 60 fps on the owner's Mac; the arrow directions against published plate-motion maps (the rotations are used as given, not re-checked).

**Next action:** G3c2 (transform offset markers). Owner: open the globe at about 150 Ma and check that the arrows look right before G3c2 is started.
