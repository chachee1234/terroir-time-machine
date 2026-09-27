# TTM Regions Roadmap

Goal: grow from one detailed region (Napa Valley) to California's main wine regions, in this order: Sonoma and Mendocino, then the rest of Northern California, then the Central Coast and Southern California. Every region is added as data, with no region-specific code (ROADMAP_CINEMATIC.md, Phase 6).

Owner request (2026-09-27): more detail in Napa, zoom to places across the Napa Valley AVA, an MVP globe around the Napa block, and a plan for the regions after it.

## Where things stand

| Layer | Napa Valley | Rest of California |
|---|---|---|
| Globe context (2 km relief, AVA outlines) | done | done, all 154 current AVAs |
| Region frame (140 m mesh, 70 m shading, faults, towns, AVAs) | done, 55 × 72 km | not started |
| Close-ups (17–51 m cells from ≈10 m source) | done, 16 sub-AVAs + Mount St. Helena | not started |
| Geologic story (chapters, section panel) | done; Mount St. Helena centred | not started |
| Soils (USDA SSURGO) | not started | not started |

The globe (`prototype/globe.html`) already shows every planned region in its phase colour. The viewer (`prototype/timemachine.html`) runs Napa and the old 30 km block.

## What changed: terrain no longer needs the Mac

The AWS Open Data Terrain Tiles (Terrarium PNGs on `s3.amazonaws.com`) are reachable from the cloud sandbox. In the U.S. they carry USGS 3DEP 1/3 arc-second (≈10 m) elevation at zoom 13 (≈15 m pixels), with ETOPO1 bathymetry offshore. `scripts/fetch_tiles.py` builds the region shading grid and all close-ups from them, and `scripts/build_globe.py` builds the globe layers. The 3DEP ImageServer is still blocked, so the Mac step is only needed for 3DEP-native products such as 1 m lidar. `prd-tnm.s3.amazonaws.com`, where USGS stages 3DEP downloads, answered from the sandbox but has not been tried for data yet.

## Make the engine region-agnostic first (one PR, before region 2)

The viewer still assumes Mount St. Helena in a few places. Each of these becomes region data:

1. **Anchor and origin.** `GNIS_UTM` is hard-coded as the scene origin and the pin. It moves to `anchor` in the region file.
2. **Chapters.** The volcano, caldera and "Today" text are inline and Napa-specific. They move to `data/regions/<id>/scenes.json` (the `SCENES.json` schema plus `span`, `camera`, `focus`). The volcano becomes optional: Sonoma Valley shares it, Paso Robles does not.
3. **Faults, towns, plate labels.** These inline arrays move to `faults.json` (GEM/UCERF3 subset clipped to the frame by a script), `places.json` (GNIS populated places) and the scenes file.
4. **UTM zone.** Zone 10 covers everything west of 120°W, which is all of Northern California and the Central Coast. Temecula (117°W) is in zone 11, so the zone becomes a region field in `fetch_terrain.py`, `fetch_tiles.py` and the viewer.
5. **AVA extraction.** `ava_extract.py` takes `--parent <ava_id>` instead of the fixed Napa Valley.
6. **Region index.** `data/regions/index.json` lists the regions with status and phase. The globe reads it instead of its inline list, and `timemachine.html?region=<id>` opens any region that has assets.

Acceptance: Napa and the 30 km block look the same as before, and a stub region with only terrain renders with generic chapters.

## Per-region pipeline (same steps each time)

1. **Region file.** The parent AVA's bounding box plus 2 km, `cell_m`, `browser_cells`, zone, anchor and close-ups (one per sub-AVA, plus named peaks).
2. **Terrain.** `fetch_tiles.py --region …` builds the frame grid, the shading grid and the close-ups. `build_globe.py` needs no change.
3. **Boundaries.** `ava_extract.py --parent …` (UC Davis, CC0).
4. **Faults.** Clip GEM/UCERF3 to the frame and record it in SOURCES.md.
5. **Geology.** Use the USGS or CGS map that covers the frame, draped as a "Today" layer, following the SIM 2956 method from M1.
6. **Soils.** Use USDA SSURGO map units for the section column and a soils layer.
7. **Story.** Write `scenes.json` with each chapter's visual class and sources. Unsupported chapters stay labelled gaps (SCIENCE_RULES).
8. **Check.** Headless run of every chapter and close-up with no console errors, a STATUS.md entry, and the globe marker switched to live.

## Order and what is new in each region

### Phase 1: Sonoma and Mendocino
| Region | Frame | New story or data |
|---|---|---|
| Sonoma Valley | Extend the Napa frame about 15 km west into a joint Napa–Sonoma frame | Same Sonoma Volcanics and Mayacamas story seen from the west. Cheapest next step. |
| Russian River Valley, Alexander Valley (+ Dry Creek) | One Northern Sonoma frame, ≈60 × 80 km | Marine terraces and Goldridge soils; the Geysers volcanic field; fog as an animated layer |
| Sonoma Coast | Coastal close-ups inside the Northern Sonoma frame; the AVA itself is too long for one frame | San Andreas fault at the coast; Pacific plate labelled on land |
| Anderson Valley | Own frame, ≈30 × 40 km | Franciscan mélange; fog through the Navarro River gap |

### Phase 2: rest of Northern California
Red Hills Lake County (Clear Lake volcanics, the youngest in the North Coast, which reuse the volcano tooling), Lodi (Sierra alluvial fans and the Delta), Sierra Foothills (granite and Gold Country metamorphics, with close-ups for El Dorado and Amador since the AVA is huge), Livermore Valley, and Santa Cruz Mountains (uplift along the San Andreas).

### Phase 3: Central Coast and Southern California
Paso Robles (calcareous soils and the Salinian granite block), Santa Maria Valley and Sta. Rita Hills (Transverse Ranges and the east-west valleys that bring in Pacific air), and Temecula Valley (Peninsular Ranges batholith; UTM zone 11).

## Detail tiers

| Tier | Cells | Where | Source |
|---|---|---|---|
| T1 globe | ≈2 km | all of California | Terrain Tiles z8 (done) |
| T2 region frame | ≈140 m mesh, ≈70 m shading | each region | 3DEP (Mac) or Terrain Tiles z13 |
| T3 close-ups | 17–51 m | each sub-AVA, key peaks | Terrain Tiles z13 (≈10 m source) |
| T4 vineyard scale (later) | 1–3 m | a few showcase vineyards | 3DEP 1 m lidar, only where it exists |
| Imagery (later) | ≈1 m | "Today" layer | USDA NAIP, public domain |

Close-ups load only when chosen, so a region's first load stays around 3 MB and each close-up adds about 0.5 MB.

## Decisions for the owner

- Phase 1 order: I recommend Sonoma Valley first, as a joint Napa–Sonoma frame, because it reuses Napa's geology and terrain work. Then Northern Sonoma, then Anderson Valley.
- Whether the globe becomes the landing page (open `globe.html` first and fly into a region) or stays a separate entry.
