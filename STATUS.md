# Status

Updated: 2026-09-12
Mode: SPECIFICATION_ONLY
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
