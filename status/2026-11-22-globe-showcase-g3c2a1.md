# 2026-11-22 · globe-showcase · G3c2a1 point-in-plate test

**Step:** G3c2a1, the first half of G3c2a (split on 2026-11-21). The side lookup itself is G3c2a2.

**Change:** new `scripts/plate_lookup.py` and `scripts/test_plate_lookup.py`. The point test sums the signed angles each edge subtends at the point, so a point inside a plate polygon gives about ±2π. The helper undoes a plate's rotation quaternion (its conjugate) so the present-day polygon can be tested at an age.

**Checks run (repo root):**
- `python3 -m unittest discover -s scripts -p 'test_*.py'`: 215 tests, OK (2 skipped). The 5 new tests pass.
- `python3 scripts/validate.py`: PASS, 0 errors, 0 warnings.
- `python3 -m compileall -q scripts`: compiled.
- pyflakes is not installed in this environment, so it was not run.

**Not verified:** the lookup on real plate polygons. Nothing in the viewer changed, so no browser or headless check was needed.

**Next action:** G3c2a2 next run: find each transform's two plates from `muller2019.json` with this test, and check that San Andreas gets the Pacific and North American plates.
