# Regions mapped in GeoLibre

Owner decision (2026-09-28): sources are found and mapped in GeoLibre, and the time machine is fed from
what is saved here. GeoLibre finds the data; the agency service it came from stays the source of record.

## Steps
1. Install the free GeoLibre desktop app (geolibre.app/downloads, or the Mac App Store). Saving a project needs the desktop app.
2. Open the region's starter project, which already has the AVA outlines and faults. In GeoLibre use Project → Open From → URL... and paste, for Sonoma Valley:
   `https://raw.githubusercontent.com/chachee1234/terroir-time-machine/main/prototype/assets/geolibre/sonoma_valley.geolibre.json`
   Until this reaches `main`, use `geolibre-link` in place of `main`.
3. Add source layers from GeoLibre's catalog panels, for example US Federal GIS → USDA → NRCS for soils, or US State GIS → California for CGS geology and DWR crop mapping.
4. Rename each source layer so it starts with its role:
   - `soils:`
   - `geology:`
   - `faults:`
   - `vineyards:`
   - `places:`

   Example: `soils: SSURGO map units`. Layers without a role (the starter outlines) are ignored.
5. Project → Save As, into this folder, named `<region_id>.geolibre` (for example `sonoma_valley.geolibre`).
6. Commit the file, or send it in the project chat. Claude then runs:
   `python3 scripts/geolibre_ingest.py data/geolibre/sonoma_valley.geolibre`

## What the ingest keeps
- **accepted:** the layer's URL is an allowed open source (USGS, USDA/NRCS, California state agencies, the UC Davis AVA and GEM fault repositories, Earth Search). It is written to `data/intake/<region_id>/<role>.geojson` and listed in `data/manifest.json` as `pending_verification` until SOURCES.md records its licence.
- **needs_review:** the layer has no URL, or is hosted somewhere we can't vouch for, such as ArcGIS Online. To accept it, add it to `<region_id>.sources.json` next to the project:
  `{"geology: county layer": {"url": "https://...", "licence": "public domain", "owner_accepted": true}}`
- **rejected:** Esri imagery or basemaps, parcel data, or any URL carrying a key or token. The sources file cannot override a rejection.
