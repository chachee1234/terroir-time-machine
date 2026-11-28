# 2026-11-25 · region-stories · S1 Petaluma Gap soils

**Step:** S1 for Petaluma Gap (the region's soils layer). E1a is ticked too: it was done on 2026-11-23 and left unticked by mistake.

**Survey areas:** found from Soil Data Access by sampling 7 × 5 points across `data/regions/petaluma_gap.json`'s frame: CA097 Sonoma County (9/15/2026), CA041 Marin County (9/16/2026) and CA055 Napa County (9/16/2026). Napa is at the frame's east edge.

**Commands run (repo root):**
- `python3 scripts/ssurgo_layers.py --frame data/regions/petaluma_gap.json --areas CA097 CA041 CA055`: 303 map units, 95 soil names, 84.9 % of the frame covered. The rest stays a labelled gap (the viewer shows no survey there).
- `prototype/assets/regions/index.json`: `soils` added to the petaluma_gap layers (one-line edit).
- `python3 scripts/validate.py`: PASS, 0 errors, 0 warnings.
- `python3 -m unittest discover -s scripts -p 'test_*.py'`: OK (2 skipped).
- Headless (harness, `timemachine.html?region=petaluma_gap&debug`): soil layer loads, 303 units; Soils chip shown; clicking it gives no page errors.

**Also changed:** SOURCES.md G45; `data/manifest.json` gets a `petaluma_gap-ssurgo-soils` entry, and the Napa soil hashes are refreshed after the E1a rebuild (they were stale).

**Not verified here:** the Soils chip in a real browser on the owner's Mac; the full browser suites (CI runs them on push).

**Next action:** S2 (geology) needs E2, which is blocked on an owner decision. The owner should check the Petaluma Gap Soils chip on the Mac.
