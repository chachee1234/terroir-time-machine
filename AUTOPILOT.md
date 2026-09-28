# Autopilot: autonomous map expansion

Owner instruction (2026-09-27): "compose prompt to autonomously keep expanding the detailed maps added to terroir time machine. Require no further dollar spend." This file is the routine's work queue and its rules. The routine is a daily Claude Code cloud session that runs on the owner's Claude subscription; no API keys, no paid services.

**Switch:** `Autopilot: ON`
Change `ON` to `OFF` (a one-line commit on `main`, or on the Start-from branch) and every run stops before doing anything. The routine can also be paused or deleted at claude.ai → Code → Routines.

**Start from:** `globe-timeline` (switch to `main` once the open PR stack is merged)
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

## Queue
Engine first (ROADMAP_REGIONS.md, "Make the engine region-agnostic first"):
- [ ] E1. Anchor and origin: move `GNIS_UTM`, the site lat/lon and the pin text into the region file; Napa and the 30 km block look unchanged.
- [ ] E2. Faults and towns as data: `data/regions/<id>/faults.json` and `places.json`, with a Tier 0 script that clips UCERF3/GEM traces to a frame.
- [ ] E3. Chapters as data: `scenes.json` per region; the volcano chapters become optional.
- [ ] E4. UTM zone as a region field in `fetch_tiles.py`, `fetch_terrain.py` and the viewer.
- [ ] E5. `ava_extract.py --parent <ava_id>`; `data/regions/index.json`; globe.html reads the index.
Phase 1 regions (one step each: region file + terrain + boundaries, then faults, then story):
- [ ] R1. Sonoma Valley: joint Napa–Sonoma frame (region file, `fetch_tiles.py`, AVAs, close-ups).
- [ ] R2. Sonoma Valley: faults (Rodgers Creek, Bennett Valley) and generic chapters.
- [ ] R3. Northern Sonoma frame (Russian River Valley, Alexander Valley, Dry Creek): terrain, AVAs, close-ups.
- [ ] R4. Northern Sonoma: faults (Maacama, Healdsburg) and chapters.
- [ ] R5. Anderson Valley frame: terrain, AVAs, close-ups, Franciscan chapter.
Present-day detail:
- [ ] D1. Soils: SSURGO map units for the Napa section column and a "Today" soils drape (Soil Data Access query script, cached).
- [ ] D2. Vineyards: replace the schematic vine tint with mapped vineyards (DWR/Land IQ, if its licence allows; else NASS CDL, public domain).
- [ ] D3. Globe: raise California to z9 (≈1 km) and add a z6 global relief option, keeping page weight under 8 MB.
Then Phase 2 regions from ROADMAP_REGIONS.md, one step each, in the listed order.
