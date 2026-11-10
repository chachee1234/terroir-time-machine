# 2026-10-10 · soil-layers

Step 1 of the soil research plan (Charlie: "the soil composition detail is still not specific enough").

- **Corison is mapped as Pleasanton loam, not Bale.** The USDA soil survey (SSURGO, Napa County CA055, version 9/16/2026) maps the winery point and the whole 150 m around it as map unit 170, Pleasanton loam, 0 to 2 percent slopes. Bale gravelly loam (from the 2024 interview) stays in the copy as "reported, unverified" until the winery confirms.
- **Real layer numbers.** The Corison section now shows the survey's sand, silt, clay, organic matter, pH and gravel for each layer (Ap, A, Bt1–Bt3 to 168 cm), with colours from the Pleasanton series description. The card, section notes and spin title read from the data instead of fixed Bale wording.
- **AVA cards** get a "Soil layers" row: the three most widespread soils in each of the 26 AVAs, with depth, texture, clay and gravel.
- **Sources page:** mapped and reported soil rows, the close-up's map units, and sand/silt/clay/organic matter columns. SOURCES.md G42.

New: `scripts/ssurgo_layers.py`, `scripts/test_ssurgo_layers.py`. Changed: `scripts/make_site.py`, `scripts/make_ava_profiles.py` (`--soils-only`).

To rebuild on a Mac, from the repo folder:

```
python3 scripts/ssurgo_layers.py --point 38.484983 -122.44736
python3 scripts/make_ava_profiles.py --region data/regions/napa_valley.json --soils-only
```

Checks: `python3 -m unittest discover -s scripts -p 'test_*.py'` (all pass), `python3 scripts/validate.py`, `node tests/lint_js.mjs`, headless Chromium of the Corison close-up, the Rutherford AVA card and sources.html (no page errors).

Gap: the Corison 100,000-year film (`corison_100ka.json`) still describes the Bale pedon's buried topsoils; left unchanged here.
