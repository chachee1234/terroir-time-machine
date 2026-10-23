# 2026-10-23 · soil-section

Charlie asked for real USDA SSURGO soils in the click-point cross-section, for the whole Napa–Sonoma frame.

- **Data.** `scripts/ssurgo_layers.py --frame data/regions/napa_valley.json` downloads the SSURGO map units of Napa County (CA055, version 9/16/2026) and Sonoma County (CA097, version 9/15/2026) through Soil Data Access, clipped to the frame, and writes `prototype/assets/regions/napa_valley/soils.png` (map unit per 30 m cell, 2540 × 2550) and `soils.json` (396 map units with slope class, components with %, drainage, depth to a restrictive layer, and layers with depth, texture, sand/silt/clay, gravel, rock fragments, organic matter, pH and available water; 95 soil names with colours). 0.57 MB + 0.64 MB. 71.4 % of the frame is covered; the rest is Lake, Solano, Marin and Yolo counties.
- **Cross-section.** Today, the column under the clicked point shows the map unit's main soil with each layer at true depth (cm scale), gravel dots, the restrictive layer as a dashed line, and the SIM 2956 unit below. The note starts "USDA SSURGO 1:24,000, map unit average, not a pit at this spot" and lists the unit's other soils, drainage, restrictive layer and plant-available water. Outside the two surveys the schematic column stays, and its note says why. The summit now shows the survey's Rock land unit over Tswt instead of the hand-written volcanic pedon.
- **Soils chip.** Drapes the soil names on today's terrain with a legend of the 12 most widespread (Bressa, Goulding, Henneke, ...). Soils and Geology are one at a time.
- **Check:** Corison falls in map unit 170, Pleasanton loam 0–2 % (same as G42), over SIM 2956 Qf.

Sources: SOURCES.md G44, `data/manifest.json` dataset `napa_valley-ssurgo-soils`.

To rebuild on a Mac, from the repo folder:

```
python3 scripts/ssurgo_layers.py --frame data/regions/napa_valley.json
```

Checks run: `python3 -m unittest discover -s scripts -p 'test_*.py'` (193 tests, OK), `python3 scripts/validate.py` (PASS), `python3 -m compileall -q scripts`, `node tests/lint_js.mjs` (PASS), `python3 scripts/security_check.py` (PASS), `node --test "tests/browser/*.test.mjs"` (see the PR), plus headless Chromium screenshots of the drape and the columns at Corison, the summit, Carneros and a point outside the surveys. pyflakes is not installable in this sandbox; CI runs it.

Gaps: the column draws only the largest major component; SIM 2956 unit names are codes with an age gloss (the published legend is not loaded); the AVA cards and the Corison site panel still use their own G42 soil data.
