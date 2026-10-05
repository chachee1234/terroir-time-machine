# Autopilot: autonomous map expansion

Owner instruction (2026-09-27): "compose prompt to autonomously keep expanding the detailed maps added to terroir time machine. Require no further dollar spend." This file is the routine's work queue and its rules. The routine is a daily Claude Code cloud session that runs on the owner's Claude subscription; no API keys, no paid services.

**Switch:** `Autopilot: ON`
Change `ON` to `OFF` (a one-line commit on `main`, or on the Start-from branch) and every run stops before doing anything. The routine can also be paused or deleted at claude.ai → Code → Routines.

**Start from:** `main` (PR #9 and #12 merged 2026-09-28)
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
- Approved by the owner 2026-10-05 (weekly audit #34): `sentinel-cogs.s3.us-west-2.amazonaws.com` (Sentinel-2 COGs, G23), `prd-tnm.s3.amazonaws.com` (USGS NHD, public domain, G26), `services.nacse.org` (PRISM 800 m normals, credit PRISM Climate Group, G29), `nassgeodata.gmu.edu` (USDA NASS CDL via CropScape, public domain, G30), `raw.githubusercontent.com/ncss-tech/SoilKnowledgeBase/` (USDA-NRCS Official Series Descriptions, G28). Viewer runtime, same date: three.js r128 from `cdn.jsdelivr.net` and fonts from `fonts.googleapis.com`.
- GPL data (owner to decide, raised by audit #34): SFEI historical ecology (G31) is GPL v3+ and ships as its own file, `prototype/assets/regions/napa_valley/historical_ecology.json`, credited to SFEI. The repo has no code licence yet, so nothing conflicts today. Open question: `build_share.py` bundles that file into the single-file share HTML alongside everything else; whether that counts as an aggregate or a combined work under the GPL is a licence interpretation the owner makes (GOVERNANCE.md §8).
- Not allowed without an owner instruction: Esri imagery, commercial basemaps, county parcel data, any source needing an account or a key.

## GeoLibre intake (owner decision, 2026-09-28)
The owner maps sources in GeoLibre and saves them as `data/geolibre/<region_id>.geolibre` (steps in `data/geolibre/README.md`). At the start of each run, if a project file there is newer than its `data/intake/<region_id>/` output, the run's one step is: `python3 scripts/geolibre_ingest.py data/geolibre/<region_id>.geolibre`, record each accepted layer's licence in SOURCES.md (or leave it `pending_verification` with the reason), and list any `needs_review` or `rejected` layers in the PR for the owner. Never edit the owner's sources file, and never accept a layer on the owner's behalf.

## Region order (owner rule, 2026-09-27)
Sonoma first, then branch out to the next AVA that touches a mapped one; when nothing touches, move to the closest AVA. `python3 scripts/region_order.py` computes the list into `prototype/assets/regions/order.json` from the UC Davis AVA outlines. A frame-sized parent AVA is mapped before its members (Northern Sonoma before Russian River Valley and Alexander Valley), and AVAs nested in a mapped frame become its close-ups. Re-run the script whenever a region is finished (pass all finished ids with `--mapped`) and take the first entry.

## Queue
Region work comes first. Each region takes three steps; any engine change a step needs is done inside that step, keeping Napa and the 30 km block unchanged.
- [x] R1–R3. Sonoma Valley: done by owner request on 2026-09-28 (branch `napa-sonoma-frame`), not as its own region. Sonoma Valley already lay inside the Napa frame, so the frame (`data/regions/napa_valley.json`, id kept) was widened into a joint Napa–Sonoma frame with `parents` [napa_valley, sonoma_valley]; its terrain, close-ups for the AVAs inside it, outlines, faults, towns, geology drape, live globe marker and Places entries are in place. Separate region files, `faults.json`, `places.json` and per-region `scenes.json` (ROADMAP_REGIONS.md items 1–3) are still to do and belong to R4.
- [ ] R4+. Next region from `prototype/assets/regions/order.json` (Petaluma Gap done 2026-09-30; next Northern Sonoma with Russian River Valley and Alexander Valley as close-ups), three steps each: (1) region file with anchor and UTM zone (ROADMAP_REGIONS.md items 1 and 4), `fetch_tiles.py --frame-grid` terrain and close-ups, `ava_extract.py --region` outlines, `make_imagery_texture.py --region` satellite texture; (2) faults, towns and generic chapters as region data (items 2 and 3); (3) live marker, Places list, headless check, and `geolibre_export.py` with the region's id added to `--regions`; add the region to `prototype/assets/regions/index.json` with its `layers`. Re-run `region_order.py --mapped` with every AVA id in `prototype/assets/ava.json` plus the finished region's.
  - [x] R4.1 Petaluma Gap step 1 (2026-09-28): `data/regions/petaluma_gap.json` (frame, `anchor`, `utm_zone`), outlines in the region's own `ava.json` (`ava_extract.py` now honours `ava_viewer`), terrain and a Sonoma Mountain close-up, Sentinel-2 texture. SOURCES G24.
  - [x] R4.2 Petaluma Gap step 2 (2026-09-29): `faults.json` (4 UCERF3 traces via GEM, new `scripts/region_faults.py`), `places.json` (towns a labelled gap: no reachable listed gazetteer covers the frame), `data/regions/petaluma_gap/scenes.json` (six shared chapters, Napa-only ones listed as gaps, a sourced "Today" card). SOURCES G24.
  - [x] R4.3 Petaluma Gap step 3 (2026-09-30): `timemachine.html?region=petaluma_gap` loads the region's own outlines, faults and chapters (Napa unchanged); `prototype/assets/regions/index.json` lists regions with a page and their layers; the globe shows Petaluma Gap as live and its label opens that page; `order.json` re-run; GeoLibre project `petaluma_gap.geolibre.json`. Headless check clean.
Present-day detail, done between regions when a region step is blocked:
- [ ] D1. Soils: SSURGO map units for the section column and a "Today" soils drape (Soil Data Access query script, cached).
- [ ] D2. Vineyards: replace the schematic vine tint with mapped vineyards (DWR/Land IQ, if its licence allows; else NASS CDL, public domain).
- [ ] D3. Globe: raise California to z9 (≈1 km), keeping page weight under 8 MB.
