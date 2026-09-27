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

