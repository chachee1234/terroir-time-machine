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
