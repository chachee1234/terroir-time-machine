# Content and data licences

This repository holds three kinds of material, each under its own terms.

## 1. Code: MIT

All source code (the viewer pages in `prototype/`, the scripts in `scripts/`, the tests and the GitHub
Actions workflows) is under the MIT License in [`LICENSE`](LICENSE), copyright 2026 chachee1234.

Bundled third-party code keeps its own licence: three.js and its OrbitControls in `prototype/vendor/`
are MIT, copyright the three.js authors (`prototype/vendor/LICENSE`).

## 2. Chapter text and documentation: CC BY 4.0

The chapter text (`SCENES.json`, `data/regions/*/scenes.json`), the on-screen descriptions written for
this project, and the documentation (`README.md`, the other `*.md` files and `prototype/sources.html`)
are licensed under the
[Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

You may share and adapt them for any purpose, including commercially, as long as you give credit, for
example: "Terroir Time Machine, chachee1234, CC BY 4.0", with a link to
https://github.com/chachee1234/terroir-time-machine, and say if you changed anything.

Quotations and facts drawn from published sources stay the work of their authors; each chapter cites
them in [`SOURCES.md`](SOURCES.md).

## 3. Datasets: their own licences

Terrain, satellite imagery, geology, faults, rivers, soils, climate, vineyard, AVA and plate-model data,
and the files derived from them in `data/` and `prototype/assets/`, keep the licence of their source.
[`SOURCES.md`](SOURCES.md) records each source, its licence and the credit it asks for, and
`prototype/sources.html` shows the same list in the viewer. In short:

| Data | Licence |
|---|---|
| USGS terrain (3DEP via AWS Terrain Tiles), geology (SIM 2956), rivers (NHD) | Public domain (U.S. Government); credit USGS |
| Copernicus Sentinel-2 imagery | Free and open; "Contains modified Copernicus Sentinel data 2026" |
| Fault traces (GEM Global Active Faults, USGS UCERF3) | CC BY-SA 4.0: derived fault files stay under CC BY-SA 4.0 |
| AVA boundaries (UC Davis Library AVA Project) | CC0 |
| Plate motion (Müller et al. 2019, EarthByte) | CC BY 3.0; cite the papers listed in SOURCES.md (G32) |
| Soils (USDA NRCS SSURGO, Official Series Descriptions), cropland (USDA NASS CDL) | Public domain (U.S. Government) |
| Climate normals and daily weather (PRISM Climate Group, Oregon State University) | Free to use with credit to PRISM |

The MIT and CC BY 4.0 grants above do not cover these datasets. If you reuse a data file, follow the
terms of its source.
