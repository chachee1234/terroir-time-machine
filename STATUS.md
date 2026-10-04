# Status

Updated: 2026-09-24
Mode: GOVERNED_AUTOMATION (see AGENTS.md, GOVERNANCE.md)
Current milestone: M1 — Evidence feasibility
Current task: M1-05 — GNIS anchor + original SIM 2956 point intersection
State: DONE WITH ONE TRANSFORMATION CHECK PENDING

## Completed in this bounded task
- Accepted the user's official USGS GNIS feature-detail export and verified Mount Saint Helena Feature ID 232163, class Summit, Sonoma County, California, primary coordinate 38.6691784 / -122.6333914, and Landform Point Type `High Point`.
- Acquired the untouched official USGS SIM 2956 Digital Database Package `sim2956c.tgz` and recorded SHA-256 `3d2feff64c8fa5448694dc9b858657ec267afc37144f009304aa0de4e5d2588e`.
- Extracted and inspected `eswn-geol.e00`; embedded PRJ = UTM zone 10, meters, Clarke 1866; FGDC datum = NAD27. Recorded the FGDC planar-grid metadata inconsistency (State Plane zone 3326 versus embedded UTM PRJ / actual coordinate magnitudes).
- Parsed the original Arc/INFO E00 topology deterministically. 10,324 arcs polygonized to 4,003 mapped faces.
- Transformed the GNIS NAD83 point into NAD27 / UTM zone 10N using the locally available PROJ operation and performed point-in-polygon.
- Result: one containing face; E00 label ID 636 / polygon 584; `ESWN-GEOL.PAT` PTYPE **Tswt**.
- Verified the published unit description: **Tswt — Welded ash-flow tuff; also includes minor partly welded and unwelded ash-flow tuff**, within Sonoma Volcanics (Pliocene and late Miocene).
- Checked mapped contacts. Under the same processing transform the nearest boundary is arc 1335, `contact, certain`, about 335.7435 m away in coverage coordinates, separating Tswt from Tslt. No overlap/no-data condition occurred.
- Did not assign the broad Sonoma Volcanics numeric age range to the point or mountain. Modern landform age remains unknown.

## Current check disposition
| Check | Status | Evidence / result | Next action |
|---|---|---|---|
| Geographic identity | **VERIFIED** | Official GNIS export: Mount Saint Helena, ID 232163 | None for identity. |
| Official GNIS point | **VERIFIED** | 38.6691784, -122.6333914; GNIS documentation = NAD83 | Preserve source precision; do not claim survey-level accuracy. |
| GNIS high-point designation | **VERIFIED** | Official record Landform Point Type = `High Point` | Do not overstate as independent survey proof of absolute highest elevation. |
| Original SIM 2956 GIS package | **VERIFIED** | `sim2956c.tgz`; original `eswn-geol.e00` acquired and checksummed | None. |
| Mapped-unit intersection | **PARTIAL** | Available deterministic transform intersects polygon 584 / ID 636 / **Tswt** | Run one high-accuracy NAD83-to-NAD27 transform using NOAA NGS NCAT/NADCON or a local NADCON grid, then repeat containment/contact check. |
| Unit description | **VERIFIED** | `Tswt` = welded ash-flow tuff; minor partly welded/unwelded ash-flow tuff | Keep map-scale limitations visible. |
| Polygon-specific numeric age | **GAP** | No numeric date established for polygon 584 by this intersection | Do not substitute the regional Sonoma Volcanics age range. |
| Modern landform age | **GAP** | No source dates present mountain morphology | Preserve gap. |

## Transformation limitation
The local PROJ installation reported that its preferred NAD83-to-NAD27 transformation grid was unavailable and used a ballpark geographic datum offset. No uncertainty radius was invented. Because the point-to-nearest mapped contact distance was calculated under that same transform, the scientific ledger keeps the unit intersection PARTIAL until one authoritative/high-accuracy datum transformation is run. NOAA NGS NCAT is an identified official route and uses NADCON for supported transformations.

## Evidence files
- `Mount Saint Helena USGS.pdf` — SHA-256 `19a305ee5cb88481d602880e47206835eeb803c1572e7289262122e654026d4a`.
- `sim2956c.tgz` — SHA-256 `3d2feff64c8fa5448694dc9b858657ec267afc37144f009304aa0de4e5d2588e`.
- `eswn-geol.e00` — SHA-256 `ccab4021858cef659d7a3d3c1b26d02ed127811171477fbead074d557c881df3`.
- `M1_GNIS_SIM2956_INTERSECTION_2026-09-12.txt` — SHA-256 `7711aead47ab617fa4f2c476fb00c6be573683d4bf54044b635d66e25e4028c0`.

## Acceptance impact
- E01: **PASS** for authoritative modern feature identity/point; GNIS explicitly designates the record point `High Point`.
- E02: **PARTIAL, materially advanced**. Original GIS polygon result is Tswt; final high-accuracy datum-transform confirmation remains.
- E03: **PASS in scope handling**. No regional Sonoma age range was promoted to a summit age.
- E04–E07: unchanged except as recorded in prior checkpoints. Do not mark all M1 complete.

## Next smallest action
Run exactly one authoritative NAD83-to-NAD27 transformation for the GNIS point using NOAA NGS NCAT/NADCON (input NAD83 realization must be documented rather than guessed), then repeat the point-in-polygon and contact check. If GNIS does not identify the NAD83 realization precisely enough to select an NCAT input frame, preserve that as the remaining transformation gap rather than inventing one.

## M1-06 datum-transform verification attempt — 2026-09-12
- NOAA NGS NCAT documentation was verified as the authoritative transformation route; it uses NADCON 5.0 and supports NAD27 plus multiple NAD83 realizations in CONUS.
- The official GNIS record supplies a generic NAD83 coordinate but does not identify a specific NAD83 realization in the retrieved evidence.
- One NCAT API execution attempt was blocked by the available runtime/network. Local PROJ confirms the preferred NADCON 5 operation/grid (`us_noaa_nadcon5_nad27_nad83_1986_conus.tif`, EPSG operation 8555, 0.15 m stated accuracy), but the grid is not installed; one official grid-download alternative was also unavailable in this runtime.
- **Mapped-unit intersection remains PARTIAL:** current result is polygon 584 / ID 636 / `Tswt`, but final authoritative datum-transform confirmation is still pending.
- No terrain, scenes, plate-model output, or application code was created.

### Next smallest action
Run the GNIS coordinate through NOAA NGS NCAT using the NAD83 realization supported by an authoritative GNIS datum statement. If GNIS continues to specify only generic NAD83, either obtain a USGS clarification/metadata statement identifying the realization or preserve this transformation ambiguity while keeping the Tswt result as partial. Do not invent a realization.

## Repository setup + governance — 2026-09-24
- Added GOVERNANCE.md (autonomous operations policy v1.0). Corrections vs. the drafted text: Opus model ID set to `claude-opus-5-5`; §9 score fixtures recomputed from the §3 rule (70, 0, 41, plus boundary cases 51 and 76); commit scope clarified (only Workflow C may push validated `regions/`/`docs/` output to main); boundary-score wording fixed; audit timing corrected to "the day before" Monday generation.
- Added `.gitignore` (`.DS_Store`). Renamed `SOURCES(1)(7).md` → `SOURCES.md` and `STATUS(1)(7).md` → `STATUS.md`.
- Initial commit `5e02e6c` pushed to https://github.com/chachee1234/terroir-time-machine (`git push -u origin main`, run by owner).
- Owner switched mode to GOVERNED_AUTOMATION (approved 2026-09-24); AGENTS.md updated to authorize only the automation GOVERNANCE.md defines.
- No workflows, scripts, pipeline code, labels, secrets or Pages settings exist yet. No scientific checks changed; the M1-06 datum-transform item above is still the open science task.

### Next smallest action
Science: unchanged — M1-06 NCAT/NADCON transform (see above). Automation: create the `AGENT_ENABLED` repo variable (set to `false` until workflows exist), then implement and test `scripts/score.py` against the §9 fixtures before any workflow is enabled.

## Tier 0 scorer — 2026-09-24
- Added `scripts/score.py` (GOVERNANCE.md §3 rule, §4 output shape; stdlib only, no network/model calls) and `scripts/test_score.py` (stdlib unittest, pytest-compatible).
- Command run: `python3 scripts/test_score.py -v` → 8 tests, all OK (5 §9 fixtures + exact-50, exact-75, upvote-cap edges). pytest is not installed; not added (dependency changes are owner decisions).
- Note: GOVERNANCE.md labels data availability "0–30 pts" but the rule awards at most 20, so the real maximum score is 90. Implemented as written; owner to decide whether to amend the label or the rule.

### Next smallest action
Owner: create repo variable `AGENT_ENABLED=false` (GitHub → Settings → Secrets and variables → Actions → Variables). Then `scripts/validate.py` + `scripts/test_validate.py` against the §9 validation fixtures. Science: M1-06 unchanged.

## Governance v1.1 — 2026-09-24
- Owner confirmed repo variable `AGENT_ENABLED=false` is created.
- Owner decision: all-linked sources award raised 20 → 30 (maximum score now 100). Updated GOVERNANCE.md §3 rule, §9 fixtures (80, 0, 41, 61, boundaries 50 and 75), version header; `scripts/score.py` and `scripts/test_score.py` updated to match.
- Command run: `python3 scripts/test_score.py -v` → 10 tests, all OK.
- Tagged `governance-v1.1` per GOVERNANCE.md §12.

### Next smallest action
`scripts/validate.py` + `scripts/test_validate.py` against the §9 validation fixtures. Science: M1-06 unchanged.

## Tier 0 validator — 2026-09-24
- Added `scripts/validate.py` and `scripts/test_validate.py` (stdlib only). Validates `SCENES.json` (the actual data contract; GOVERNANCE.md §9's "TIMELINE.json" refers to it) with the SCENES_README.md semantic checks: unique IDs; older_ma ≥ younger_ma; scenes and keyframes oldest→youngest; keyframes inside scene interval; claim/asset/source/model/anchor references resolve; asset files exist and match bytes/SHA-256; source IDs missing from SOURCES.md → warning.
- Commands run: `python3 scripts/test_validate.py -v` → 11 tests OK (§9 fixtures: repo manifest passes, missing ledger entry warns, 750 Ma in 1000–500 passes, 100 Ma in 50–40 fails). `python3 scripts/validate.py` → PASS, 0 errors, 1 warning (jsonschema not installed, full schema check skipped). `python3 scripts/test_score.py` → OK.
- Not implemented: release-mode gates (review status, rights, nonempty manifest), claim time/scope coverage of frames, visual-class/label semantics. These remain planned M2 checks, not passed.
- Full JSON Schema validation needs the `jsonschema` package; not installed (dependency changes are owner decisions).

### Next smallest action
Owner: decide whether to add `jsonschema` as a validation dependency. Next Tier 0 piece: `scripts/deploy.py` with a `--dry-run` test (§9). Science: M1-06 unchanged.

## Validation dependency — 2026-09-24
- Owner approved adding `jsonschema`. Added `requirements.txt` (`jsonschema==4.26.0`), a local `.venv/` (git-ignored) created with `python3 -m venv .venv && .venv/bin/pip install jsonschema`.
- Added 2 schema tests to `scripts/test_validate.py` (skip when jsonschema is absent).
- Commands run: `.venv/bin/python scripts/validate.py` → PASS, 0 errors, 0 warnings. `.venv/bin/python scripts/test_validate.py` → 13 tests OK. `python3 scripts/test_validate.py` (system Python, no jsonschema) → OK, 2 skipped.

### Next smallest action
`scripts/deploy.py` with a `--dry-run` test (GOVERNANCE.md §9). Science: M1-06 unchanged.

## Tier 0 deploy step — 2026-09-24
- Added `scripts/deploy.py` (Workflow C deploy; stdlib + optional jsonschema) and `scripts/test_deploy.py`.
- Behavior: `deploy.py <region_id> <score> [--dry-run] [--no-push]`. Checks region ID format, score 0–100, `regions/<id>/SCENES.json` exists and passes validate + schema; refuses if any working-tree change is outside `regions/`/`docs/` (GOVERNANCE.md §3 commit scope). Then copies to `docs/regions/<id>`, commits only those paths ("Auto-generated: <id>, Score: <n>"), tags `auto-YYYYMMDD-HHMMSS-<id>`, pushes main and the tag. `--dry-run` performs only the read-only checks.
- Commands run: `.venv/bin/python scripts/test_deploy.py --dry-run -v` → 7 tests OK (all in throwaway temp git repos; no push). Score/validate suites re-run OK under `.venv` and system Python. `python3 scripts/deploy.py nope 80 --dry-run` → correctly refused (missing region).
- Assumption to confirm: a generated region is a folder `regions/<id>/` containing its own `SCENES.json`; asset paths are resolved from the repo root. The generator (`src/pipeline/generate_region.py`) does not exist yet, so this layout is provisional.
- Not done: never run against this repo for real; no workflow calls it yet.

### Next smallest action
Owner: confirm or change the region folder layout. Tier 0 scripts named in GOVERNANCE.md still missing: `scripts/digest.py`. Then the GitHub Actions workflows (all gated on `AGENT_ENABLED`, currently false). Science: M1-06 unchanged.

## Tier 0 digest — 2026-09-24
- Owner confirmed the region layout `regions/<id>/SCENES.json` used by `scripts/deploy.py`.
- Added `scripts/digest.py` and `scripts/test_digest.py` (stdlib only, no network). Reads `gh issue list --json number,title,state,labels,closedAt,comments` on stdin; reports issues closed and regions generated in the last 7 days, top 5 `backlog` issues by latest posted "Score: N/100", open `type:audit-flag` issues, open `generation-failed` issues as alerts, and `--tests`/`--alert` inputs. Avg confidence and Pages uptime are printed as "not measured" (no deterministic source yet).
- Commands run: `.venv/bin/python scripts/test_{score,validate,deploy,digest}.py` → all OK (10 + 13 + 7 + 5 tests).
- GOVERNANCE.md inconsistency noted, not changed: §3 table says digest assembly Sunday 4 PM UTC; §5 Workflow E and §13 say 17:00 (after the 16:00 audit). Workflow will use 17:00 unless the owner says otherwise.

### Next smallest action
All Tier 0 scripts named in GOVERNANCE.md exist. Next: GitHub Actions workflows (issue intake, Monday generation, Sunday audit, Sunday digest), each gated on `AGENT_ENABLED` (currently false) — needs owner review before merge because workflow YAML is a security-sensitive change. Science: M1-06 unchanged.

## Automation workflows (branch `automation-workflows`, for owner review) — 2026-09-24
- Added `.github/workflows/region-intake.yml` (Workflows A/B), `monday-generation.yml` (C), `sunday-audit.yml` (D), `sunday-digest.yml` (E). Every job is gated at job level on `vars.AGENT_ENABLED == 'true'` (currently false). Top-level `permissions: {}`; each job requests only what it needs; model jobs are read-only and separate from the jobs that write issues. Actions pinned to commit SHAs (claude-code-action v1 `9171db3`, checkout v7 `3d3c42e`).
- Model jobs: Haiku `claude-haiku-4-5-20251001` (max 3 turns) and Opus `claude-opus-5-5` (max 3 turns), auth via `CLAUDE_CODE_OAUTH_TOKEN` secret, tools limited to Read, output forced to a JSON schema (`--json-schema` → `structured_output`).
- Added helpers: `scripts/intake.py` (+ `test_intake.py`, 7 tests), `scripts/ensure_labels.sh`, `scripts/summarize_tests.py`.
- Commands run: `.venv/bin/python -m unittest discover -s scripts -p 'test_*.py'` → 42 tests OK. Workflow lint (scratch venv, PyYAML): all 4 files parse; `bash -n` OK on every run step; embedded Python compiles; both JSON schemas pass `Draft202012Validator.check_schema`. Inline audit formatter, comment classifier and test summarizer exercised with sample input.
- NOT run on GitHub: no workflow has executed. `CLAUDE_CODE_OAUTH_TOKEN` secret not yet created. `src/pipeline/generate_region.py` does not exist (Monday job exits with a notice).
- Decisions made, for owner review: effort comes from a developer label `effort:<hours>h` (absent → scored as high effort, cannot auto-approve); upvotes = 👍 reactions on the issue; model runs only for maintainer-applied `region-request` labels and owner/member/collaborator comments (quota protection); digest posted as an issue labeled `digest` (GOVERNANCE allows discussion or email); region ID = `issue-<number>`, data file `data/issue-<number>.json`, generator called as `generate_region.py <data file> <output dir>`.
- GOVERNANCE.md issues found, not changed: §7 kill-switch snippet uses a step-level `exit 0`, which does not stop later steps — workflows use a job-level `if` instead. Needs-data 7-day auto-close (§3 table) not implemented.

### Next smallest action
Owner: review and merge the `automation-workflows` pull request; add repo secret `CLAUDE_CODE_OAUTH_TOKEN` (`claude setup-token`). Keep `AGENT_ENABLED=false` until then; first live test via workflow_dispatch of the digest (no model use). Science: M1-06 unchanged.
- GOVERNANCE.md v1.2 (owner-approved, on this branch): `claude setup-token` tokens are valid 1 year (as printed by Claude Code 2.1.282); rotation reminder at 11 months; rotate immediately on exposure. Tag `governance-v1.2` to be applied after merge to main.

## First live runs + intake schema fix (branch `fix-intake-schema`) — 2026-09-25
- Owner enabled automation (`AGENT_ENABLED=true`, `CLAUDE_CODE_OAUTH_TOKEN` secret added). PR #1 merged (`eecaa43`); tag `governance-v1.2` pushed on `7c80f4d`.
- Sunday digest via workflow_dispatch: run 36105325034 success; issue #2 posted, tests 42/42 on the runner.
- Region intake on issue #3 (Crater Lake test): run 36106437203 failed. Auth worked; Haiku finished with result subtype success but no `structured_output` (annotation: "--json-schema was provided but Claude did not return structured_output"). Cause: extraction schema used features structured outputs do not support (numeric min/max, type arrays, nested objects without `additionalProperties: false`). Issue left unchanged, as designed.
- Fix: schema rewritten with supported features only (anyOf for nullables, strict nested objects); range rules moved to Tier 0 `scripts/intake.py` (lat/lon out of range → null, confidence outside 0–1 → extraction-failed, age ≤ 0 or uncertainty ≥ age dropped, gnis_id ≤ 0 → null); failure message no longer blames only the token. Added `scripts/test_workflows.py` to reject unsupported schema features in any workflow.
- Commands run: `.venv/bin/python -m unittest discover -s scripts -p 'test_*.py'` → 47 tests OK; region-intake.yml parses (PyYAML).

### Next smallest action
Owner: review/merge the `fix-intake-schema` PR, then re-trigger issue #3 (remove and re-add `region-request`). Expected: Score 70/100 → backlog. Science: M1-06 unchanged.

## UI prototype + modern terrain (branch `ui-prototype`) — 2026-09-27
- Owner asked to see an MVP UI and approved fetching terrain for the AOI.
- Added `prototype/index.html`: static tour (6 stops, play/pause, keyboard, scene URL, evidence panel, reduced-motion) using only M1 ledger facts; unsupported chapters render as labeled gaps. Not the M2 Vite/TypeScript app.
- Added `scripts/fetch_terrain.py` (stdlib; downloads with curl because this Mac's python.org build lacks CA certs). One 3DEP request; raw file in git-ignored `data/raw/`; `data/manifest.json` records URL + hashes; browser grid `prototype/assets/terrain.bin` (224×224 Int16, ≈99.5k triangles). Source recorded as G16 in SOURCES.md.
- Vendored Three.js 0.186.1 (MIT) `three.module.js`, `three.core.js`, `OrbitControls.js`, LICENSE into `prototype/vendor/` (~2 MB uncompressed).
- Checked in the browser pane at desktop width and 375×812: terrain renders, rotate/zoom, 1×/2× vertical exaggeration labeled, reset view; gap scenes hide terrain and pin; no horizontal scroll; no console errors. Not tested: WebGL-failure fallback, touch devices, performance on a reference device.
- Commands: `python3 scripts/fetch_terrain.py` then `--from-raw --out-cells 224`.

### Next smallest action
Drape the SIM 2956 geologic units (Tswt and neighbours, from `eswn-geol.e00`) on the terrain as a labeled mapped layer. Science: M1-06 unchanged.

## Cinematic viewer (branch `cinematic-viewer`) — 2026-09-27
- Added `prototype/timemachine.html` (1.8 Ga → today, globe to 30 km diorama, labeled stylized/illustrated/terrain classes) and `ROADMAP_CINEMATIC.md` (Phase 1, step 1). Added `<meta charset="utf-8">` so `·`, `◀`, `≈`, `×` don't render garbled under `python3 -m http.server`.
- Checked with `cd prototype && python3 -m http.server 8000` in headless Chromium (SwiftShader), 4× speed: played to "Today" and the Replay state, final shot loaded `assets/terrain.bin` ("USGS 3DEP terrain · 1,323 m"), no page or console errors. The sandbox blocks the three.js CDNs, so r128 was served from the identical npm package. Not tested: 60 fps on the MacBook Air, touch devices.
- Viewer edits (owner request): compass, schematic fault traces on the surface and in the block's cut faces (thrusts 150–28 Ma, strike-slip after 28 Ma), stream network and rain from priority-flood drainage on the modern grid, 50 m contours + town labels for the last ~10 ka, a 200-year "Today" mini-timeline with vineyards from the mid-1800s, and an optional cross-section panel (top right, off by default) for owner approval. Per-pixel hillshade/contours now read the full DEM grid; a finer grid needs `python3 scripts/fetch_terrain.py --from-raw --out-cells 512` on the Mac (3DEP is not reachable from the cloud sandbox). Headless playback: no console errors.
- Faults and plates (owner request): the local strike-slip lines are now the mapped Maacama and Collayomi traces (UCERF3 via GEM, SOURCES.md G17), active from ~8 Ma when subduction ended at this latitude; the old thrusts stay schematic. The globe shows stylized continent edges, collision zones, Laurentia's western rift (≈760–540 Ma) and subduction margin (from ≈260 Ma), and plate names; the block labels the Farallon, Pacific and North American plates.

## Napa Valley expansion, step 1 (branch `napa-valley-region`) — 2026-09-27
- Owner goal: map all of Napa Valley. Added `data/regions/` (`mt_st_helena.json` = current block, `napa_valley.json` = AVA bbox + 2 km, ~55 × 72 km) and `fetch_terrain.py --region` (rectangular grids, per-region asset folder). Added `scripts/ava_extract.py` (UC Davis AVA Project, CC0, SOURCES.md G18) and `scripts/test_ava.py`; `python3 -m unittest discover -s scripts -p 'test_*.py'` → 54 tests OK (2 skipped, as before). The viewer drapes the AVA outlines at "Today", labels the ones inside the block, and shows a valley locator with the block's footprint.
- Next smallest action (owner's Mac, 3DEP is blocked from the cloud sandbox): `python3 scripts/fetch_terrain.py --region data/regions/napa_valley.json`, then make the viewer's local scene read the region grid instead of the fixed 30 km square.

## Napa Valley expansion, step 2 (branch `napa-valley-scene`) — 2026-09-27
- Owner ran `python3 scripts/fetch_terrain.py --region data/regions/napa_valley.json` on the Mac (commit "Add Napa Valley 3DEP terrain": 393×512 grid, raw 1843×2400 @ 30 m, 0 no-data cells, range −2.3 to 1317.5 m, maximum cell at the GNIS summit).
- The viewer's diorama is now region-driven: it loads `assets/regions/napa_valley/terrain.*` by default (`?region=mt_st_helena` gives the old 30 km block) and sizes mesh, walls, water, fog, camera, drainage, DEM texture, AVA layer and section profile from the frame. Eras before today (S1, S2, and S3/S4 under the volcano) are now built from the smoothed measured surface, so every era keeps the real valley layout (roadmap step 10). Added the mapped faults inside the frame (Rodgers Creek–Healdsburg, West Napa, Bennett Valley, Green Valley, Hunting Creek–Berryessa and –Bartlett Springs connector, Hayward north end, Great Valley thrusts; UCERF3 via GEM, G17) and valley town labels. Headless Chromium, both regions, key ages: no console errors.
- Next smallest action: owner review; then real soils (USDA SSURGO) for the section column, and geology for the eastern hills.

## Napa detail, close-ups, MVP globe, regions plan (branch `napa-explore-globe`) — 2026-09-27
- Owner asked for more detail in Napa, zooming to places across the Napa Valley AVA, an MVP globe around the Napa block, and a plan for further wine regions.
- Finer terrain without the Mac: the AWS Terrain Tiles host is reachable from the cloud sandbox (SOURCES.md G19). Added `scripts/fetch_tiles.py` (stdlib: PNG decoding, inverse UTM, caching in git-ignored `data/raw/tiles/`). Ran `python3 scripts/fetch_tiles.py --region data/regions/napa_valley.json`. That wrote `dem_hi` (787×1024, ≈70 m; 2× finer shading for the whole valley) and 17 close-up grids (16 sub-AVAs plus a new `close_ups` entry for Mount St. Helena, 17–51 m cells).
- Viewer: a **Places** panel (and clickable AVA names) flies the camera to any sub-AVA or Mount St. Helena and loads its close-up. The close-up is a finer mesh that plays every era: its older stages are sampled from the valley stages, and streams are re-traced with inflow from the valley network. It also gets its own thin AVA outlines, 10 m contours and fine vine rows. `?loc=<id>` opens a close-up directly. The scale bar adapts from 10 km to 500 m, and contours no longer fill flat lakes.
- Added `prototype/globe.html`, the MVP globe: Earth relief, California at 2 km with relief exaggerated 4×, all 154 California AVAs, the Napa 3DEP block set into it with walls and a rim, and the planned regions coloured by phase. The intro flies Earth → California → Napa, and links open the viewer and its close-ups. Assets come from `python3 scripts/build_globe.py`.
- Added `ROADMAP_REGIONS.md`: engine generalisation first (anchor, chapters, faults and towns as data, UTM zone, region index), then Sonoma & Mendocino → rest of Northern California → Central Coast & Southern California.
- Checks: headless Chromium (SwiftShader) with no console errors for the valley, 4 close-ups (switching between them) and the globe's three views. Added `scripts/test_tiles.py`; `python3 -m unittest discover -s scripts -p 'test_*.py'` → 60 tests OK (2 skipped, as before). Not tested: frame rate on the MacBook Air (a close-up adds up to 262k vertices), touch devices.
- Next smallest action: owner review; then the region-agnostic engine PR from ROADMAP_REGIONS.md.

## Globe through the whole timeline, plate animation, global relief, autopilot (branch `globe-timeline`) — 2026-09-27
- Owner asked to stay in globe view through the timeline and zoom into the Mount St. Helena 30 km area with the globe greyed where nothing is known, to start present-day topography for the whole globe, to animate the subduction, to weigh a list of data sources, and to set up an autonomous prompt that keeps expanding the maps.
- Viewer (`prototype/timemachine.html`): the globe is now drawn in every era. Below 186 Ma one camera flies from orbit down to the block (altitude on a log scale); the block sits on the globe at true scale, the globe outside it is grey ("not reconstructed") until the present, and at Today the globe shows real relief (California at 2 km, the rest ≈10 km). The dive frames the Mount St. Helena 30 km area. You can zoom from the block out to the whole planet in any era. The white "veil" is gone.
- New **Plates** panel: an animated section of the Farallon plate sinking beneath North America, with the Franciscan wedge, arc magma, corner flow, the ridge, slab window and Sonoma Volcanics. Opens by itself at 250 Ma; labelled illustration (SOURCES.md G20).
- Globe relief rebuilt at 4096×2048 from z4 tiles: `python3 scripts/build_globe.py --ava-file <cached avas.geojson>` (new `--earth-zoom`, `--earth-width` flags). Globe page reads the texel size from the image. Label dots in both pages now sit on their points (they were offset by half the label width).
- Added `AUTOPILOT.md` (queue and rules for the daily routine) and a data-source table in ROADMAP_REGIONS.md.
- Checks: `python3 -m unittest discover -s scripts -p 'test_*.py'` → 60 tests OK (2 skipped). Headless Chromium (SwiftShader) at 1800, 300, 178, 150, 100, 60, 17, 15, 5, 1 Ma and Today, zoom-outs to 600 and 9000 km at Today and 150 Ma, and globe.html: no console errors. Not tested: frame rate on real hardware, touch zoom-out.
- Next smallest action: owner review; the routine then starts on AUTOPILOT.md step E1.

## One program, click-point section, minimizable card, Sonoma-first order (branch `globe-timeline`) — 2026-09-27
- Owner asked for the time machine and globe as one program, the cross-section at the clicked point, a minimizable description box, and region order: Sonoma first, then the next AVA in the area, then the closest AVA.
- `timemachine.html` now carries the globe page's content: at Today the globe shows all 154 California AVAs coloured by the plan (live, next three, later) with clickable region names; clicking flies there and the card describes the region with "Back to Napa Valley" and "All regions". A **Regions** chip replaces the Globe link; `?view=regions` and `?site=<ava_id>` open it. `globe.html` now only forwards old links.
- Click (not drag) anywhere on the block: the section moves to that point (SW–NE, ±14.5 km, clipped to the frame), opens, and an orange curtain plus a dot mark the cut. The column says what is and is not known for that point (schematic away from the mapped summit rock).
- The description card has a minimize button (remembered per browser).
- New `scripts/region_order.py` (Tier 0, stdlib) writes `prototype/assets/regions/order.json`; AUTOPILOT.md queue now starts with Sonoma Valley and follows that file. Added `scripts/test_region_order.py`.
- Checks: `python3 -m unittest discover -s scripts -p 'test_*.py'` → 61 tests OK (2 skipped). Headless Chromium: eras 1800/250/150/8/0 Ma, the 30 km block, `globe.html` redirect, regions view, flights to Sonoma Valley and Mendocino, card minimize, click-to-section: no console errors. Not tested: touch devices, real-hardware frame rate.
- Next smallest action: owner review of PR #11; the nightly routine starts on AUTOPILOT R1 (Sonoma Valley).

## Open in GeoLibre (branch `geolibre-link`, stacked on `one-program`) — 2026-09-27
- Owner asked to analyze GeoLibre (github.com/opengeos/GeoLibre, MIT) for integration, then said "proceed" on step 1 of the proposal: an "Open in GeoLibre" link per region.
- New `scripts/geolibre_export.py` (Tier 0, stdlib) writes `prototype/assets/geolibre/<id>.geolibre.json` plus `index.json`: GeoLibre projects with inline GeoJSON for the AVA outline, the AVAs inside it, mapped faults near it (read from the viewer's FAULTS table, UCERF3 via GEM) and, for mapped regions, the viewer's 3D frame. Napa Valley (mapped, full-resolution outlines, 575 KB) and Sonoma Valley (planned, simplified outlines, 12 KB).
- Viewer: the card shows "Open in GeoLibre ↗" at Today for the live region and on region cards that have a project. The link is `web.geolibre.app/?url=<raw.githubusercontent.com URL>` on the ref in `index.json` (`main`); `?glref=<branch>` overrides it for testing before merge.
- Added `scripts/test_geolibre_export.py`; SOURCES.md T04; AUTOPILOT R3 now re-runs the export.
- Commands: `python3 scripts/geolibre_export.py`; `python3 -m unittest discover -s scripts -p 'test_*.py'` → 66 tests OK (2 skipped); GeoLibre's own `parseProject` (esbuild bundle of packages/core/src/project.ts at d9d7651) accepted both files; headless Chromium: link appears at Today and on the Sonoma Valley card, not at 1800 Ma or on Petaluma Gap (no project), no console errors.
- Not tested: opening the projects in the live GeoLibre app (web.geolibre.app is blocked from the cloud sandbox). The links use `main`, so they return 404 until this branch reaches `main`.
- Next smallest action: owner opens the Sonoma link with `?glref=geolibre-link` and confirms it loads; then step 2 (slope, aspect and sun exposure at the clicked point).

## GeoLibre intake (branch `geolibre-link`) — 2026-09-28
- Owner: "we need to find a different way to integrate geolibre for source information. But want it mapped and used to feed data to the terroir time machine." Plan posted in the thread; GeoLibre becomes the place sources are found and mapped, and the time machine reads what is saved.
- New `scripts/geolibre_ingest.py` (Tier 0, stdlib): reads `data/geolibre/<region_id>.geolibre`. Layers named `soils:`, `geology:`, `faults:`, `vineyards:` or `places:` get a verdict from their recorded source URL: accepted (allowed open hosts), needs_review (no URL or unknown host; owner can accept in `<region_id>.sources.json`) or rejected (Esri imagery, parcels, keyed URLs). Accepted layers go to `data/intake/<region_id>/<role>.geojson` (features touching the frame, kept whole) and into `data/manifest.json` as `pending_verification`.
- `data/geolibre/README.md` gives the owner's steps; AUTOPILOT.md has a "GeoLibre intake" rule; SOURCES.md T04 updated. The starter projects from `geolibre_export.py` stay as the map to start from.
- Commands: `python3 -m unittest discover -s scripts -p 'test_*.py'` → 76 tests OK (2 skipped), including the new `scripts/test_geolibre_ingest.py` (synthetic project: accepted, needs_review, rejected, owner override, re-import, dry run).
- Not tested: a project actually saved by GeoLibre with catalog layers (GeoLibre's site is blocked from the sandbox), so where each catalog panel records its service URL is unconfirmed; the ingest reports needs_review when it finds none. The viewer does not read `data/intake/` yet.
- Next smallest action: owner saves `data/geolibre/sonoma_valley.geolibre` with soils and geology layers; then wire accepted soils into the section column (AUTOPILOT D1).

## Phase 2 chapters as data + SIM 2956 geology drape (branch `phase2-scenes`) — 2026-09-28
- Phase 1 merge: the cinematic viewer (PR #7) and its follow-ups are on `main`; PRs #9, #12 and #13 were merged on 2026-09-28. Phase 1 acceptance: plays start to finish, last frame on 3DEP terrain, no console errors in headless Chromium: checked. 60 fps on a MacBook Air: **not tested** (headless SwiftShader runs at about 1 fps).
- A. Chapters as data: the 13 chapters moved from the viewer's `CH` array into `SCENES.json` → `chapters` (id, age_ma, span_ma, tag, title, body, visual_class, key; plus optional `scale` and `dwell_s`, which two chapters already used). `SCENES.schema.json` gains `$defs.chapter` with `span_ma` and `visual_class` (reconstruction-stylized | illustration | measured-approx). The viewer fetches `../SCENES.json` at startup and keeps a built-in copy as the fallback; `scripts/sync_viewer_data.py` rewrites that copy and a test fails when the two differ. Plate keyframes moved to `data/plates/stylized.json` (class reconstruction-stylized, labelled), loaded the same way. `scripts/validate.py` checks chapters oldest to youngest, `span_ma[0] >= age_ma >= span_ma[1]`, unique ids, and the plates file.
- B. Geology drape: new `scripts/make_geology_texture.py` (stdlib; GDAL is not installed and nothing was added) reads the owner-supplied `eswn-geol.e00` (SHA-256 matches M1-05) and rasterizes PTYPE onto the terrain grid: `prototype/assets/geology.png` (224 × 224, 51 units) for the 30 km block and `prototype/assets/regions/napa_valley/geology.png` (393 × 512, 88 units) for the default Napa frame, each with `geology_legend.json`. Its reader reproduces M1-05: the summit is polygon 584 / ID 636 / Tswt. NAD27 → NAD83 by the three-parameter CONUS mean (not NADCON; SOURCES.md G21). Viewer: a **Geology** chip drapes the map on today's terrain (fades out before about 60,000 years ago), with a legend of the largest units and the label "USGS SIM 2956, 1:100,000"; unmapped areas stay plain terrain.
- Commands: `python3 -m pip install -r requirements.txt` (jsonschema, already listed, so schema tests now run instead of skipping); `python3 scripts/make_geology_texture.py data/raw/eswn-geol.e00`; `python3 scripts/make_geology_texture.py data/raw/eswn-geol.e00 --terrain prototype/assets/regions/napa_valley/terrain.json --out-dir prototype/assets/regions/napa_valley`; `python3 scripts/sync_viewer_data.py`; `python3 scripts/validate.py` → PASS; `python3 -m unittest discover -s scripts -p 'test_*.py'` → all pass, 0 skipped.
- Headless Chromium, repo root served (`python3 -m http.server` at the repo root, open `/prototype/timemachine.html`): all 13 chapter ticks, Play, Today, Geology on and off at Today and at 18.8 Ma, the 30 km block with its drape, and SCENES.json blocked (falls back to the built-in copy): no console errors. When only `prototype/` is served, `../SCENES.json` is out of reach and the viewer uses its built-in copies by design.
- Not tested: real-hardware frame rate; touch devices.
- Next smallest action: owner review of the PR; then Phase 3 step 9 (imagery texture) or unit descriptions for the legend from the SIM 2956 pamphlet.

## Joint Napa–Sonoma frame (branch `napa-sonoma-frame`, stacked on `phase2-scenes`) — 2026-09-28
- Owner: "continue developing area with same detail around napa valley". Sonoma Valley already lay almost entirely inside the Napa frame, so the frame was widened rather than starting a separate region: `data/regions/napa_valley.json` (id kept so links keep working) now spans ≈76 × 77 km, west to Santa Rosa, Sebastopol and Healdsburg and south over the whole Sonoma Valley AVA, with `parents` Napa Valley and Sonoma Valley.
- Terrain: new `fetch_tiles.py --frame-grid` builds the mesh grid `terrain.bin` (546 × 548, ≈140 m) from AWS Terrain Tiles (3DEP ≈10 m source) in the same layout as the 3DEP request, which is blocked from the sandbox. Over the old frame it differs from the owner's 3DEP grid by mean −0.5 m, RMS 7.9 m; the summit is the highest cell in both. `dem_hi` (1020 × 1024) and all close-ups rebuilt; 552 tiles (174 new).
- AVAs: `ava_extract.py --region` keeps the parents, their nested AVAs and every AVA wholly inside the frame: 28 outlines, 26 close-ups (10 new: Bennett Valley, Chalk Hill, Crystal Springs, Fountaingrove District, Guenoc Valley, Knights Valley, Moon Mountain District, Solano County Green Valley, Sonoma Mountain, Suisun Valley).
- Faults: Rodgers Creek–Healdsburg now runs to Healdsburg and the San Andreas (North Coast) crosses the south-west corner (same GEM/UCERF3 file, G17). Towns: Sonoma, Glen Ellen, Kenwood, Santa Rosa, Petaluma, Rohnert Park, Sebastopol, Windsor, Healdsburg (approximate positions, as before; SOURCES.md G22).
- Geology drape re-rasterized on the new grid (546 × 548, 93 units); SIM 2956 covers about 42 % of the frame, the rest stays plain terrain.
- Globe and plan: every AVA in the frame is live on the globe, Sonoma Valley's name flies home, `order.json` re-run with those ids (next: Petaluma Gap, then Northern Sonoma). GeoLibre Napa project re-exported with both parent AVAs. AUTOPILOT R1–R3 marked done this way; R4 carries the region-data engine work.
- Commands: `python3 scripts/ava_extract.py --from-file <cached avas.geojson>`; `python3 scripts/fetch_tiles.py --region data/regions/napa_valley.json --frame-grid`; `python3 scripts/make_geology_texture.py data/raw/eswn-geol.e00 --terrain prototype/assets/regions/napa_valley/terrain.json --out-dir prototype/assets/regions/napa_valley`; `python3 scripts/region_order.py --mapped <the 28 AVA ids in prototype/assets/ava.json>`; `python3 scripts/geolibre_export.py`; `python3 scripts/sync_viewer_data.py`; `python3 scripts/validate.py` → PASS; `python3 -m unittest discover -s scripts -p 'test_*.py'` → 94 tests OK.
- Headless Chromium (repo root served): Today on the wider frame, Geology on, Places list, Sonoma Mountain and Fountaingrove District close-ups, `?region=mt_st_helena`, regions view and the Petaluma Gap card: no console errors. Not tested: real-hardware frame rate (the frame has 22 % more mesh cells), touch devices.
- Next smallest action: owner review; then geology for the Santa Rosa Plain and eastern Napa (needs the owner to supply the USGS/CGS map files, since USGS is blocked here), or AUTOPILOT R4 (Petaluma Gap).

## Satellite texture, automated (branch `satellite-texture`) — 2026-09-28
- Owner: "satellite texture. compose code for automating the development" (ROADMAP_CINEMATIC Phase 3, item 9).
- Source: Sentinel-2 L2A true colour from the AWS Open Data bucket `sentinel-cogs` (reachable; USDA NAIP hosts, Earth Search's STAC API and Planetary Computer are blocked from the sandbox). SOURCES.md G23.
- New `scripts/make_imagery_texture.py` (Tier 0, stdlib): finds the Sentinel-2 grid squares covering a region frame, lists the dry-season scenes in the bucket, reads their STAC items and picks the clearest complete one, reads only the needed tiles of the 40 m overview by HTTP range requests (own TIFF/DEFLATE/predictor reader), crops to the frame and writes `imagery.jpg` (own baseline JPEG encoder) and `imagery.json`, plus a manifest entry. No manual step; `--scene` pins a scene. Picked `S2A_10SEH_20260714_0_L2A` (14 July 2026, 0 % cloud) from 126 scenes.
- Outputs: `prototype/assets/regions/napa_valley/imagery.jpg` (1905 × 1912, 1.8 MB) and `prototype/assets/imagery.jpg` (750 × 750, 0.27 MB).
- Viewer: a **Satellite** chip drapes the image on today's terrain and close-ups (fades out before about 60,000 years ago), with the date and Copernicus credit in the legend; vine tint dims under it. Geology still draws on top when both are on.
- Automation: ROADMAP_REGIONS per-region pipeline step 5b and AUTOPILOT R4 step (1) now run the script for every new region.
- Commands: `python3 scripts/make_imagery_texture.py --region data/regions/napa_valley.json` (search) and `--region data/regions/mt_st_helena.json --scene S2A_10SEH_20260714_0_L2A`; `python3 scripts/validate.py` → PASS; `python3 -m unittest discover -s scripts -p 'test_*.py'` → 100 tests OK (new `scripts/test_imagery_texture.py`: grid squares, scene choice, tiled COG window read, JPEG structure, committed textures match their frames). Both JPEGs decode in Chromium.
- Headless Chromium (repo root served): Satellite on at Today in the joint frame, the Sonoma Mountain close-up and the 30 km block; legend hidden at older ages; no console errors. Not tested: real-hardware frame rate, touch devices.
- Next smallest action: owner review; a 10 m image per close-up (same script, overview 0) if the 40 m drape looks too soft up close.

## Shareable single-file HTML for reviewers (branch `share-html`, stacked on `satellite-texture`) — 2026-09-28
- Owner: "I need to get feedback from other people and need to share through html not claude. move this project to html". The viewer already is HTML, but it needs a web server for its data files and the repo is private, so there was no way to hand it to someone outside Claude.
- New `scripts/build_share.py` (stdlib) writes `dist/terroir-time-machine.html` (git-ignored): one file with all 79 viewer data files embedded (Int16 grids delta-coded and gzipped, JSON gzipped, images as is) and a fetch()/TextureLoader shim, so it opens by double-click from a download, email or shared drive. 18.5 MB. GeoLibre project files are left out (the viewer never loads them). three.js and fonts still come from their CDNs, so reviewers need internet.
- New `prototype/share/feedback.html`, injected only into the shared build: a Feedback chip with a notes panel that records what was on screen with each note (age, chapter card, view, layers, place), keeps notes in the browser, and saves them as a .txt file or copies them to paste into an email. Nothing is sent anywhere.
- Tests: `scripts/test_build_share.py` (3 tests: Int16 coding round trip on a real grid, every literal fetch path embedded, built page self-contained and in the right script order). Full suite 103 OK (1 skipped).
- Headless Chromium from file:// (CDN three.js served locally because the sandbox blocks the CDN): default region at Today with Geology and Satellite, a close-up, `?region=mt_st_helena`, `?view=regions`: no console errors, no failed requests; the feedback panel saved a notes file. Not tested: Safari, Firefox, phones, real email clients.
- Commands: `python3 scripts/build_share.py`; `python3 -m unittest discover -s scripts -p 'test_*.py'`.
- Next smallest action: owner review; rebuild the file after each merge with `python3 scripts/build_share.py`.
## Viewer edits: trackpad move, 10 m satellite close-ups, subduction on the globe (branch `viewer-edits`) — 2026-09-28
- Owner edits: satellite detail near the present ("sentinel satellite imagery goes back 25 years"), plate subduction shown on the globe rather than in a cross-section window, and two fingers to move the map north, south, east, west.
- Move: a two-finger trackpad swipe pans the map over the ground (pinch still zooms; a notched mouse wheel still zooms), right-drag pans with a mouse, two-finger drag pans on touch screens; the target is clamped to the frame plus 15 %. On the globe a swipe turns the globe. Also restored `lCtl.maxPolarAngle`, damping and target, which a trailing `//` comment had swallowed.
- Satellite: on by default, so it fades in by itself as the slider reaches today (same fade as before, about the last few thousand years of the log axis). New `make_imagery_texture.py --closeups/--closeups-only` crops the frame's scene (S2A_10SEH_20260714) at 10 m for all 27 close-ups (`detail/<id>.imagery.jpg`, 20 MB, `detail/imagery.json`, manifest, SOURCES G23); a close-up uses its own texture and the legend says "10 m close-up". Correction recorded for the owner: Sentinel-2 L2A starts mid-2015 (about 11 years), not 25; Landsat reaches 25+ years at 30 m but is not reachable from this sandbox.
- Plates: during the subduction era (fades in 262–248 Ma; hidden once the real map shows) a pit opens in the globe at Laurentia's stylized western margin, moving with it, and the existing "Plates in motion" section plays on its north wall: ocean plate with moving stripes bending into the trench and sinking, the Franciscan wedge, arc magma, later the slab window and sideways sliding. Illustration class, labelled on the wall "section enlarged 3×, geometry schematic". The globe camera looks into the pit from the south while it is open. On the block it shows only when zoomed out to the planet. The Plates chip toggles the pit on the globe and still opens the panel on the block; the panel no longer opens by itself.
- Not done: a detailed published plate model. Merdith 2021 and Cao 2024 (SOURCES G12, G14) are rights-unresolved and Zenodo/EarthByte/GPlates hosts are blocked from the sandbox; the continents stay the stylized blobs.
- Tests: `scripts/test_imagery_texture.py` adds the close-up check (scene matches the frame, bbox matches the index, JPEG size, 10 m). Suite 101 OK (1 skipped), validate PASS. Headless Chromium (repo served, CDN three.js served locally): default region at Today, Rutherford close-up (legend "10 m close-up"), 240/200/120/40 Ma, `?region=mt_st_helena`, `?view=regions`: no console errors; wheel-event pan checked numerically (moves, clamps, notched wheel zooms). Not tested: a real trackpad or touch screen, Safari, Firefox.
- Commands: `python3 scripts/make_imagery_texture.py --region data/regions/napa_valley.json --closeups-only`; `python3 -m unittest discover -s scripts -p 'test_*.py'`; `python3 scripts/validate.py`.
- Owner decision (2026-09-28, decision card): keep the stylized continents, no published plate model. Done: continents now follow a smooth Hermite path through the same keyframes (no stop at each keyframe; checked it passes through every keyframe with no jumps), plate labels end "· stylized", legend reads "Continent edge, stylized (hand-drawn, not a plate model)". Also removed a built `dist/` file that had been committed by mistake on this branch (the branch was rebuilt without it).
- Next smallest action: owner review; optional year-by-year Sentinel-2 imagery 2016–2026 for the recent-years view.

## Globe stays wide until 28 Ma; slower dive (branch `viewer-edits`) — 2026-09-28
- Owner: "the animation zoom at 150 ma is way too close up ... stay zoomed out on the globe and animate the geologic plate movement that takes place until 28 ma, have the zoom be slower and smoother."
- prototype/timemachine.html: the dive from globe to ground moved from 186–150 Ma to 27–10 Ma (`A_DIVE`, `A_LAND`), eased with smootherstep, altitude falling on a log scale. Until then the globe camera rests with the whole planet in view (`G_END`), follows more slowly, and faces the subduction pit from the same distance; the pit closes 34–29 Ma as subduction here ends. Globe light now comes from over the viewer's shoulder so the visible side is lit. During the dive the planet stays stylized until about 900 km up, then turns grey (not reconstructed).
- SCENES.json: 150 Ma card is now "This spot is deep ocean" (globe view, same facts; the block-only thrust sentence removed); 28 Ma card says the view drops to the ground from there. Synced with scripts/sync_viewer_data.py.
- Checked: unit tests and validate pass; Playwright screenshots (swiftshader) at 250, 150, 66, 30, 24, 21, 19, 16, 12, 8 Ma and today, no page errors.
- Next smallest action: owner looks at the new share copy and PR #19.

## Autopilot R4.1: Petaluma Gap region data (branch `autopilot`) — 2026-09-28
- Daily routine run; `Autopilot: ON`; `autopilot` branch created from main (did not exist).
- Added `data/regions/petaluma_gap.json`: Petaluma Gap AVA box plus 2 km (≈61 × 34 km), `utm_zone` 10, `anchor` = computed box centre (labelled as such).
- `scripts/ava_extract.py` now writes a non-Napa region's viewer outlines to the region file's `ava_viewer` path and keys the manifest entry by region id; Napa's `prototype/assets/ava.json` is byte-identical. New test in `scripts/test_ava.py`.
- Built terrain (436 × 242 mesh, 1024 × 568 shading, Sonoma Mountain close-up; 228 z13 tiles) and a 40 m Sentinel-2 texture (27 July 2026). SOURCES G24; manifest updated by the scripts.
- Repairs: one. The first terrain fetch hit a transient empty reply (curl exit 52) on one tile; retried with the tile cache reused from the main worktree and it completed.
- Commands: `curl -sSf -o data/raw/ava/avas.geojson <UC Davis avas.geojson>`; `python3 scripts/ava_extract.py --region data/regions/petaluma_gap.json --from-file data/raw/ava/avas.geojson`; `python3 scripts/fetch_tiles.py --region data/regions/petaluma_gap.json --frame-grid`; `python3 scripts/make_imagery_texture.py --region data/regions/petaluma_gap.json`; `python3 -m unittest discover -s scripts -p 'test_*.py'` (OK, 1 skipped); `python3 scripts/validate.py` (PASS).
- Headless check: not run, because no page changed; the viewer does not load this region until step 3.
- Next smallest action: R4.2, faults, towns and generic chapters for Petaluma Gap as region data.

## Autopilot R4.2: Petaluma Gap faults, towns, chapters (branch `autopilot`) — 2026-09-29
- Daily routine run; `Autopilot: ON`; main unchanged since yesterday, merged into `autopilot`; 1 step was awaiting review.
- New `scripts/region_faults.py` (stdlib) clips the GEM active-faults file (G17) to a region frame into `<assets_dir>/faults.json`; tests in `scripts/test_region_faults.py`. Petaluma Gap: San Andreas (North Coast), Rodgers Creek–Healdsburg, Hayward (north), Bennett Valley.
- Towns: gap, recorded in `prototype/assets/regions/petaluma_gap/places.json` (Natural Earth has none in the frame; GNIS/Census blocked). Needs an owner decision on another source (for example OpenStreetMap) if labels are wanted.
- Chapters: `data/regions/petaluma_gap/scenes.json`, six shared planet-scale chapters by id, four gaps, two not applicable, one sourced "Today" card (AVA date and counties from UC Davis, terrain maximum from the G24 grid, fault names from G17).
- Repairs: none.
- Commands: `python3 scripts/region_faults.py --region data/regions/petaluma_gap.json --from-file <cached GEM geojson, SHA-256 37babb51…>`; `curl -sSf -o data/raw/ne/ne_10m_populated_places_simple.geojson <Natural Earth GitHub raw>` (SHA-256 matches G22); `python3 -m unittest discover -s scripts -p 'test_*.py'` (OK, 1 skipped); `python3 scripts/validate.py` (PASS).
- Headless check: not run, because no page changed.
- Next smallest action: R4.3, live marker, Places list, headless check and GeoLibre export for Petaluma Gap.

## Autopilot R4.3: Petaluma Gap in the viewer (branch `autopilot`) — 2026-09-30
- Daily routine run; `Autopilot: ON`; main unchanged, `autopilot` already current; 2 steps were awaiting review.
- prototype/timemachine.html: for a region other than Napa or the 30 km block (`OWN`), loads `assets/regions/<id>/ava.json`, replaces the fault table with `faults.json`, and builds chapters from the shared ids plus `data/regions/<id>/scenes.json`. When Mount St. Helena lies outside the frame (`SUMMIT_IN` false) the camera stays on the frame centre and the summit pin is hidden. The subtitle shows the region name. The geology drape is only requested when the region index lists it.
- New `prototype/assets/regions/index.json` (regions with a page, their parents and layers). The globe's regions layer labels every indexed region; clicking a mapped region that has another page opens `?region=<id>`.
- `region_order.py --mapped` re-run with Petaluma Gap: next is Northern Sonoma. `geolibre_export.py` uses a region's own `faults.json` when present; `petaluma_gap.geolibre.json` added (Napa and Sonoma projects byte-identical). `build_share.py` bundles `data/regions/*/scenes.json`.
- Places: the Places panel lists the region's close-up (Sonoma Mountain) from `detail/index.json`. The approximate town labels already in the viewer (G22: Petaluma, Rohnert Park, Glen Ellen, Sonoma) show where they fall in the frame; the Petaluma Gap `places.json` gap stands.
- Checks: unit tests OK (1 skipped); validate PASS; headless Chromium (swiftshader) with no console errors and no failed requests: `?region=petaluma_gap` at 250 Ma, 20 Ma and today, default page at today, `?view=regions`, and the Petaluma Gap globe label opening `?region=petaluma_gap`.
- Repairs: one. The first headless run logged a 404 for the absent geology legend; fixed by the index `layers` check.
- Commands: `python3 scripts/region_order.py --mapped <28 Napa-frame AVA ids>,petaluma_gap`; `python3 scripts/geolibre_export.py --regions napa_valley,sonoma_valley,petaluma_gap`; `python3 -m unittest discover -s scripts -p 'test_*.py'`; `python3 scripts/validate.py`; Playwright scripts in the session scratchpad.
- Next smallest action: owner review of PR 20 (3 steps); next region R4 Northern Sonoma step 1.

## Autopilot branch: main merged after PR #19 (branch `autopilot`) — 2026-10-01
- PR #19 merged into main; merged main into `autopilot` (merge commit, no rebase). STATUS.md conflict resolved by keeping both sides.
- The merged viewer asks every region for `detail/imagery.json` (10 m close-up drape); Petaluma Gap had none, which logged a 404. Built it with `python3 scripts/make_imagery_texture.py --region data/regions/petaluma_gap.json --closeups-only` (Sonoma Mountain, 10 m) and listed `closeup_imagery` in `prototype/assets/regions/index.json`.
- Checks: unit tests OK (1 skipped); validate PASS; headless Chromium with no console errors or failed requests on `?region=petaluma_gap` (20 Ma, today), the default page and `?view=regions`.
- Next smallest action: owner review of PR 20.
## Deep terroir: Corison site, rivers, close-up geology, share links, sources page (branch `deep-terroir`, stacked on `viewer-edits`) — 2026-09-30
- Owner: focus TTM on extreme detail in soil composition, historic rivers, climate, erosion and vineyard acreage, shown with animated cross-sections, starting at Corison (Bale gravelly loam, "an ancient river crossing the property"); also approved the mapped.earth ideas (timeline captions, share links, sources page).
- Sources check from the sandbox: reachable are AWS S3 (USGS National Map staged products, NOAA nClimGrid, Terrain Tiles, Sentinel-2) and GitHub raw. Blocked by the network policy: USDA Soil Data Access (SSURGO), USGS NGMDB and pubs, PRISM, CropScape, California DWR crop mapping, SFEI. The owner will allow them from a computer later.
- New: `scripts/make_rivers.py` (NHD rivers, G26); `make_geology_texture.py --closeups` (G27); `scripts/make_site.py` + `data/sites/corison.json` (G28); `fetch_tiles.py --only <id>` and per-site `cell_m`/`kind` in region `close_ups`; `prototype/sources.html`.
- Viewer: Rivers chip and legend; close-ups drape their own finer geology (legend lists the close-up's units); Places has a vineyard group (Corison); choosing Corison flies close, pins it, opens a wider section panel that lays down the layers (hills, fan gravel and sand, flood loam burying two old topsoils, soil forming) beside the Bale soil column, with a Replay button and a site card; a caption over the timeline shows the current chapter; Share (bottom bar) copies a link with `t` (age, Ma), `loc` and `cam`; Sources link in the bottom bar.
- Commands: `python3 scripts/fetch_tiles.py --region data/regions/napa_valley.json --zoom 15 --only corison`; `python3 scripts/make_imagery_texture.py --region data/regions/napa_valley.json --closeups-only`; `python3 scripts/make_geology_texture.py data/raw/eswn-geol.e00 --out-dir prototype/assets/regions/napa_valley --closeups`; `python3 scripts/make_rivers.py --region data/regions/napa_valley.json`; `python3 scripts/make_site.py data/sites/corison.json --e00 data/raw/eswn-geol.e00 --half 2450`; `python3 scripts/validate.py` → PASS; `python3 -m unittest discover -s scripts -p 'test_*.py'` → all pass (new `scripts/test_rivers_site.py`, 8 tests).
- Headless Chromium (repo root served, three r128 served locally): `?t=0&loc=corison` (card, pin, section at several animation moments), `&cam=` shared camera, Rivers with Satellite off: no page errors. Not tested: real-hardware frame rate, phones, Safari.
- Next smallest action: owner review; after the owner allows the blocked hosts, SSURGO polygons and horizons under each vineyard (replacing "reported"), the SFEI historical channels, PRISM climate at 800 m and vineyard fields/acreage.

## Deep terroir data: PRISM climate and CDL vineyard acreage (branch `deep-terroir`) — 2026-10-01
- Owner allowed the data hosts in the cloud environment. Reachable now: PRISM (services.nacse.org), CropScape, data.cnra.ca.gov, ngmdb/pubs.usgs.gov, sdmdataaccess. The new environment no longer reaches PyPI, npm, raw.githubusercontent.com or AWS S3 (the earlier defaults), so `make_site.py` cannot re-fetch the OSD and `make_rivers.py` cannot re-fetch NHD in this environment.
- New: `scripts/make_climate.py` → `climate.json` (G29); `scripts/make_vineyards.py` → `vineyards.json` + `vineyards.png` (G30); `make_site.py` adds a `climate` block from climate.json (Corison: Winkler Region III, 861 mm/yr); `scripts/test_climate_vineyards.py` (5 tests).
- Not done: SSURGO under Corison (USDA's Soil Data Access is failing on their side); SFEI historical channels (Cloudflare blocks scripts). See SOURCES.md "Gaps after the 2026-10-01 host change".
- Commands: `python3 scripts/make_climate.py --region data/regions/napa_valley.json`; `python3 scripts/make_vineyards.py --region data/regions/napa_valley.json`; `python3 -m unittest discover -s scripts -p 'test_*.py'` → 117 pass, 1 skipped; `python3 scripts/validate.py`.
- Next smallest action: retry SSURGO; owner uploads the SFEI zip; viewer chips for Climate and Vineyards (data is in place, not drawn yet).

## SFEI historical channels and habitats (branch `deep-terroir`) — 2026-10-01
- Owner uploaded the SFEI Napa Historical Ecology GIS zip (sfei.org blocks scripts). New `scripts/make_historical_ecology.py` (stdlib file-geodatabase reader) → `historical_ecology.json` (G31); `make_site.py` adds a `historical` block (habitat at the site, SFEI channels crossing the section line; refactored `line_crossings`); new `scripts/test_historical_ecology.py` (4 tests).
- Finding: Corison sits in SFEI's Valley Oak Savanna; no historical channel or paleochannel under it; nearest historical channel 0.96 km SW, paleochannels ~1.7 km NE by the river. The "ancient river" is not mapped by SFEI; a prehistoric fan channel remains possible (Qf fan, stratified gravelly alluvium) but unmapped.
- Command: `python3 scripts/make_historical_ecology.py --zip <uploaded zip> --region data/regions/napa_valley.json`; tests 121 pass, 1 skipped.
- Next smallest action: viewer layer for historical channels/habitats (toggle "1800s") and climate/vineyards; retry SSURGO.

## Real continent motion on the globe (branch `plate-model`) — 2026-10-01
- Owner asked to analyse open plate-movement databases and refine the plate animation. Chosen: Müller et al. 2019 (+ Young 2019 to 410 Ma), CC BY 3.0, from GPlates/pygplates-tutorials (G32). Merdith 2021 / Cao 2024 sit on Zenodo, unreachable here.
- New `scripts/make_plate_model.py` → `prototype/assets/plates/muller2019.json`; the globe now draws the model's continents from 410 Ma to today (fading in from the stylized blobs at 430–400 Ma). The Napa marker, Laurentia's label and the western trench ride the North American plate; trench teeth and chevrons stay on the ocean side of the real coast.
- New `scripts/test_plate_model.py` (7 tests). `python3 -m unittest discover -s scripts -p 'test_*.py'` → 128 pass, 1 skipped; `python3 scripts/validate.py` PASS.
- Headless Chromium at 410/250/150/60/30/5 Ma: Pangaea at 250 Ma, Gulf of Mexico opening at 150 Ma, marker on the coast at 60/30 Ma. Not tested: real-hardware frame rate (the mask redraws when the age changes), phones.
- Command: `python3 scripts/make_plate_model.py --src <pygplates-tutorials checkout>`.
- Next smallest action: owner review; optional plate-boundary lines (the model's topologies) or past shorelines (paleogeography) if wanted.


## Autopilot R4.1: Northern Sonoma step 1 (branch `autopilot`) — 2026-10-01
- `autopilot` restarted from main (PR #20 merged). New `data/regions/northern_sonoma.json` (≈48 × 65 km frame, computed anchor, `utm_zone` 10, `frame_cut_avas`); nine AVA outlines in `prototype/assets/regions/northern_sonoma/ava.json` (Napa's `ava.json` unchanged); terrain (320 z13 tiles, 110 newly fetched) with eight close-ups; Sentinel-2 40 m texture and 10 m close-up images (asset folder ≈22 MB). SOURCES G33.
- Repairs (2): `test_ava.py` failed because Rockpile and Pine Mountain-Cloverdale Peak run past the frame. (1) Widened the frame west and north: the wider frame takes in the coast, where the tiles give spurious depths to ≈−14,900 m, so it was dropped and the original terrain regenerated from cache. (2) The test now accepts a nested AVA past the edge only when the region file lists it in `frame_cut_avas` and it still has vertices inside; the viewer paints outlines on a canvas, so they are clipped at the frame.
- Known limits: a north–south brightness seam on land where the S2A and S2B scenes meet; bytes downloaded from Sentinel were not measured (tiles well under the 600 cap).
- Commands: `python3 scripts/ava_extract.py --region data/regions/northern_sonoma.json --from-file data/raw/ava/avas.geojson`; `python3 scripts/fetch_tiles.py --region data/regions/northern_sonoma.json --frame-grid`; `python3 scripts/make_imagery_texture.py --region data/regions/northern_sonoma.json` and `--closeups-only`; `python3 -m unittest discover -s scripts -p 'test_*.py'` → 133 pass, 1 skipped; `python3 scripts/validate.py` → PASS. No page touched (the viewer does not load this region until R4.3), so no headless check this step.
- Next smallest action: owner review; R4.2 Northern Sonoma faults, towns and chapters.

## Autopilot R4.2: Northern Sonoma step 2 (branch `autopilot`) — 2026-10-02
- Region data for faults, towns and chapters: `prototype/assets/regions/northern_sonoma/faults.json` (San Andreas North Coast, Maacama, Rodgers Creek–Healdsburg, Bennett Valley, Collayomi); `places.json` (Santa Rosa only, Natural Earth; other towns a gap pending a source or the owner's OpenStreetMap decision); `data/regions/northern_sonoma/scenes.json` (six shared chapters, six Napa-staged chapters listed as gaps, a "Today" card from G17/G18/G19/G33). `test_region_faults.py` now checks both region files. SOURCES G33. No downloads (cached GEM and Natural Earth files).
- Commands: `python3 scripts/region_faults.py --region data/regions/northern_sonoma.json --from-file <cached GEM geojson, SHA-256 37babb51…>`; `python3 -m unittest discover -s scripts -p 'test_*.py'` → Ran 134 tests, 1 skipped, all pass; `python3 scripts/validate.py` → PASS. No page touched (the viewer loads this region in R4.3), so no headless check this step.
- Next smallest action: owner review of PR #28; R4.3 Northern Sonoma live page, index entry, globe marker, GeoLibre export.

## Autopilot R4.3: Northern Sonoma step 3 (branch `autopilot`) — 2026-10-03
- `timemachine.html?region=northern_sonoma` opens the region with its own outlines, five faults, chapters ("Northern Sonoma today") and town labels. Region pages now read towns from the region's `places.json` (Northern Sonoma: Santa Rosa; Petaluma Gap: none, its recorded gap) instead of showing the Napa frame's hand-placed town list. Repair 1: region pages asked for `rivers.json`, which they don't have (404 since PR #22 added rivers); they now fetch it only when `regions/index.json` lists `rivers` under `layers` (shared `OWN_LAYERS`, also used for geology).
- `prototype/assets/regions/index.json` gains Northern Sonoma; `region_order.py --mapped` re-run with northern_sonoma, so the globe shows it live; next region: West Sonoma Coast. `geolibre_export.py --regions …,northern_sonoma` adds `northern_sonoma.geolibre.json` (other projects byte-identical).
- Known: the Collayomi fault shows as "Collayami" on region pages (the GEM catalog's spelling).
- Commands: `python3 scripts/region_order.py --mapped <previous list>,northern_sonoma`; `python3 scripts/geolibre_export.py --regions napa_valley,sonoma_valley,petaluma_gap,northern_sonoma`; `python3 -m unittest discover -s scripts -p 'test_*.py'` → 134, 1 skipped, all pass; `python3 scripts/validate.py` → PASS. Headless Chromium (swiftshader, three r128 served locally): `?region=northern_sonoma` at 250, 20 and 0 Ma, `?region=petaluma_gap`, default Napa page and `?view=regions`: no page errors and no failed requests after the fix. Not tested: real-hardware frame rate, phones, Safari.
- Next smallest action: owner review of PR #28 (Northern Sonoma, three steps); then R4 West Sonoma Coast step 1 on a fresh branch from main after merge.

## Autopilot R4.1: West Sonoma Coast step 1 (branch `autopilot`) — 2026-10-04
- New `data/regions/west_sonoma_coast.json` (≈65 × 53 km frame, computed anchor, `utm_zone` 10, `pit_floor_m` −200); four AVA outlines in `prototype/assets/regions/west_sonoma_coast/ava.json` (Napa's unchanged); terrain (340 z13 tiles) with three close-ups; Sentinel-2 40 m texture and 10 m close-ups (asset folder ≈8 MB). SOURCES G34.
- Repair 1: the first terrain pass showed coastline pits down to ≈−16,000 m (the problem that stopped the wider Northern Sonoma frame). `fetch_tiles.py` gained an opt-in per-region `pit_floor_m`: tile pixels below it are set to 0 m and counted (manifest and `terrain.json`). A first floor of −100 m also flattened real ETOPO1 shelf (−100 to −113 m in the south-west tiles), so the floor is −200 m: 2,824 pixels changed, raw range now −112.8 to 1055.1 m. New test in `test_tiles.py`; `test_ava.py` checks the new outline file.
- Known limits: a north–south brightness seam on land where the S2A and S2B scenes meet; near-shore sea is a flat 0 m in the tiles, not bathymetry. Newly fetched tile count and Sentinel bytes not measured (340 tiles in total, under the 600 cap).
- Commands: `python3 scripts/ava_extract.py --region data/regions/west_sonoma_coast.json --from-file data/raw/ava/avas.geojson`; `python3 scripts/fetch_tiles.py --region data/regions/west_sonoma_coast.json --frame-grid` (then `--offline` re-runs); `python3 scripts/make_imagery_texture.py --region data/regions/west_sonoma_coast.json` and `--closeups-only`; `python3 -m unittest discover -s scripts -p 'test_*.py'` → 136, 1 skipped, all pass; `python3 scripts/validate.py` → PASS. No page touched, so no headless check this step.
- Next smallest action: owner review of PR #28 (now four steps); R4.2 West Sonoma Coast faults, towns, chapters.
