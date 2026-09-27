# Autopilot: autonomous map expansion

Owner instruction (2026-09-27): "compose prompt to autonomously keep expanding the detailed maps added to terroir time machine. Require no further dollar spend." This file is the routine's work queue and its rules. The routine is a daily Claude Code cloud session that runs on the owner's Claude subscription; no API keys, no paid services.

**Switch:** `Autopilot: ON`
Change `ON` to `OFF` (a one-line commit on `main`, or on the Start-from branch) and every run stops before doing anything. The routine can also be paused or deleted at claude.ai → Code → Routines.

**Start from:** `napa-valley-scene` (switch to `main` once PR #9 is merged)
**Working branch:** `autopilot` (one PR, never merged by the routine)

## Rules for each run
1. Read AGENTS.md, STATUS.md, this file, and only the sections of ROADMAP_REGIONS.md, SCIENCE_RULES.md and SOURCES.md the step needs. AGENTS.md and GOVERNANCE.md win over this file.
2. If the switch is OFF, or the `autopilot` PR already holds 5 unreviewed steps (checked items below marked `[x]` with no owner "reviewed" note since the last merge), stop and write nothing.
3. Do the first unchecked step only. One bounded step per run; two repair attempts at most, then mark the step `[!] blocked: <reason>` and stop.
4. Data: only open-licensed sources already listed in SOURCES.md or in "Allowed sources" below, fetched with the repo's Tier 0 scripts. At most 600 terrain tiles or 150 MB per run. Raw downloads stay in git-ignored `data/raw/`. Record every new dataset in SOURCES.md (licence, URL, date) and `data/manifest.json`.
5. Science: no invented facts, ages, rates or licences. Anything not backed by a listed source is a labelled gap or schematic (SCIENCE_RULES.md).
6. Check: `python3 -m unittest discover -s scripts -p 'test_*.py'` passes, and a headless Chromium run of every page touched shows no console errors. Never mark an untested check as passed.
7. Commit to `autopilot` only; push; open the PR if none is open (base: the Start-from branch), else update its description. Never merge, never push to `main`, never force-push.
8. Tick the step here, add a STATUS.md entry with the exact commands and the next action, and end with a short summary of what changed and what the owner should look at.

## Allowed sources (beyond SOURCES.md)
- AWS Open Data Terrain Tiles (G19), UC Davis AVA Project (CC0), USGS UCERF3 via GEM (CC BY-SA 4.0), USGS/CGS geologic maps (public domain), USDA NRCS SSURGO via Soil Data Access (public domain), California DWR/Land IQ crop mapping (check the dataset's stated licence first), Sentinel-2 L2A via Earth Search STAC (Copernicus open licence, attribution required), USDA NAIP (public domain).
- Not allowed without an owner instruction: Esri imagery, commercial basemaps, county parcel data, any source needing an account or a key.

## Region order (owner rule, 2026-09-27)
Sonoma first, then branch out to the next AVA that touches a mapped one; when nothing touches, move to the closest AVA. `python3 scripts/region_order.py` computes the list into `prototype/assets/regions/order.json` from the UC Davis AVA outlines. A frame-sized parent AVA is mapped before its members (Northern Sonoma before Russian River Valley and Alexander Valley), and AVAs nested in a mapped frame become its close-ups. Re-run the script whenever a region is finished (pass all finished ids with `--mapped`) and take the first entry.

## Queue
Region work comes first. Each region takes three steps; any engine change a step needs is done inside that step, keeping Napa and the 30 km block unchanged.
- [ ] R1. Sonoma Valley: region file (frame = AVA bounding box plus 2 km, anchor, close-ups for its nested AVAs), `fetch_tiles.py` terrain and close-ups, AVA outlines. This needs the anchor and UTM zone to come from the region file (ROADMAP_REGIONS.md items 1 and 4).
- [ ] R2. Sonoma Valley: mapped faults (Rodgers Creek, Bennett Valley; UCERF3 via GEM) as `faults.json`, towns as `places.json`, and generic chapters in `scenes.json` (ROADMAP_REGIONS.md items 2 and 3).
- [ ] R3. Sonoma Valley: switch its marker to live on the globe, add it to the Places list, headless check of every chapter and close-up. Re-run `python3 scripts/geolibre_export.py --regions napa_valley,sonoma_valley` so its "Open in GeoLibre" project uses the new region file and full-resolution outlines.
- [ ] R4+. Next region from `prototype/assets/regions/order.json` (currently Petaluma Gap, then Northern Sonoma with Russian River Valley and Alexander Valley as close-ups), three steps each as above; R3's GeoLibre re-run adds the region's id to `--regions`.
Present-day detail, done between regions when a region step is blocked:
- [ ] D1. Soils: SSURGO map units for the section column and a "Today" soils drape (Soil Data Access query script, cached).
- [ ] D2. Vineyards: replace the schematic vine tint with mapped vineyards (DWR/Land IQ, if its licence allows; else NASS CDL, public domain).
- [ ] D3. Globe: raise California to z9 (≈1 km), keeping page weight under 8 MB.
