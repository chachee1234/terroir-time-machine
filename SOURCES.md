# Source registry and research structure

Discovery checked 2026-09-12. This is a seed registry, not a completed geological literature review. Linked abstract/catalog content was inspected where stated; no GIS payloads, rotation files or full geological maps were downloaded. No source here approves local paleotopography. M1 must resolve the outstanding gaps before producing scientific scene content.

## Seed scientific sources
| ID | Primary source | Checked content / permitted current use | Limitations and next action |
|---|---|---|---|
| G01 | Mankinen (1972), [Paleomagnetism and potassium-argon ages of the Sonoma Volcanics, California](https://www.usgs.gov/publications/paleomagnetism-and-potassium-argon-ages-sonoma-volcanics-california) | USGS abstract read; it connects Mount St. Helena rocks with the Gauss normal epoch and reports 5.3 to about 2.9 Ma for sampled volcanic rocks | Historical study; this is not a dated modern mountain shape. Retrieve full methods/sample locations and compare later local work. Paper/figure reuse rights unresolved. |
| G02 | Wagner et al. (2011), [Geology, geochronology, and paleogeography of the southern Sonoma volcanic field and adjacent areas](https://www.usgs.gov/publications/geology-geochronology-and-paleogeography-southern-sonoma-volcanic-field-and-adjacent), DOI 10.1130/GES00626.1 | USGS abstract read; gives a broader Sonoma Volcanics interval of about 8–2.5 Ma and discusses regional displacement | Southern field/regional scope. Do not assign its full interval, displaced centers or fault offsets to Mount St. Helena. Full local applicability and rights pending. |
| G03 | Merdith et al. (2021) supporting [1 Ga plate model, Zenodo record 4485738](https://zenodo.org/records/4485738), DOI 10.5281/zenodo.4485738 | Dataset landing page read; version 1.1b, accompanying last-1-Ga model identified | Payload and license not inspected; license text not exposed in retrieved page. Verify rights, paper, reference frame and model limitations before redistribution. Select and pin one version, not a mixture. No local summit backtracking. |
| G04 | [USGS 3DEP 1/3 arc-second DEM collection](https://data.usgs.gov/datacatalog/data/USGS%3A3a81321b-c153-416f-98b7-cc8e5f0e17c3) | Catalog discovery only; candidate modern terrain input | M1/M3 must verify exact tile metadata, coverage, units, datums, acquisition epoch and rights. Cell spacing is not an accuracy guarantee. |
| G05 | [USGS Open-File Report 97-500 landing page](https://pubs.usgs.gov/of/1997/of97-500/) | Search lead only; direct read returned 403 | Unverified candidate, not admitted evidence. Verify title, authors, locality, scale and usable files before registration. Do not infer contents from report number. |
| G06 | [NGMDB product record 30834](https://ngmdb.usgs.gov/Prodesc/proddesc_30834.htm) | Search lead only; direct read returned 403 | Unverified; may be unsuitable. Confirm identity and locality before using. |

G01 and G02 have different study scopes; their numbers must not be combined into a single Mount St. Helena chronology. Searches also returned Mount St. Helens, Washington material; those results were excluded. The absence of a verified detailed local map is an explicit M1 blocker for local reconstruction, not a reason to improvise.

## Tool and hosting references
| ID | Reference | Use |
|---|---|---|
| T01 | [Three.js license](https://github.com/mrdoob/three.js/blob/dev/LICENSE) | MIT license inspected; pin package version and retain license at M2 |
| T02 | [GPlates official site](https://www.gplates.org/) | Describes offline reconstruction tools and GPLv2 license; verify selected distribution at M2 |
| T03 | [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) | Public repositories supported on GitHub Free; published site ≤1 GB and soft bandwidth limit 100 GB/month at this check. Educational MVP use must comply with current terms; recheck at release. |

## Required source record structure
For evidence/sources.json, one object per independently licensed/versioned source or asset:
- id, full citation, authors, year, title, publisher, DOI, canonical URL, version.
- kind: paper / map / dataset / software / service_terms.
- verification: candidate / metadata_verified / content_verified; verified_by, verified_at, checked_scope (abstract/full text/figure/data payload).
- temporal coverage and spatial coverage; nominal scale/resolution; CRS, vertical datum, units if geographic.
- access date; exact locators; concise evidence note; known conflicts/limitations.
- license/rights statement, rights URL, redistribution: allowed / prohibited / unresolved, required attribution; distinguish file components.
- download URL and checksum for each used file, original filename, byte size; null until actually fetched.
- supersedes/superseded_by IDs where applicable; never silently erase historical interpretations.

Do not fill missing fields with plausible guesses. A candidate source can stay in the research ledger but cannot back a published scientific claim. A schema source record is a compact runtime subset; full bibliographic and spatial metadata remains in the authoring ledger.

## Required claim record structure
Use the claim definition in SCENES.schema.json: ID, statement, evidence class, spatial scope, geological interval, confidence and reason, evidence references with exact locators, limitations and review. Record supporting and conflicting sources separately in the full ledger. If a source disagrees, set review pending until reconciled; preserve the resolution note. Never claim a source reviewed when only an abstract was read.

## Required derived asset manifest
ID; local path; SHA-256; bytes; scientific/aesthetic role; source IDs and input hashes; claim IDs; recipe path/version/hash; exact parameters; software versions; CRS/datum transforms; simplification/resampling tolerance; output resolution; license/attribution; model/reference frame/age when applicable. File paths must be relative, traversal-free and locally packaged. Production browsers do not fetch arbitrary URLs from the evidence ledger.

## M1 research queue and stopping rule
1. Verify modern summit identity and AOI from authoritative mapping.
2. Find the most appropriate local geologic map and associated unit descriptions/dates; inspect actual map coverage, legend and sample locations. Compare G01/G02 carefully, including newer work if found.
3. Verify a redistributable global model reaching 1000 Ma and inspect its scientific limitations.
4. Verify terrain tile and rights. Use coarse resolution if sufficient for the budget.
5. Compile 6–10 narrowly phrased claims for the core tour, with explicit gaps for unsupported ages and geometry.

Per research question: inspect up to three strong primary candidates first. If unresolved, record the exact missing evidence and expand only that question; do not re-read the entire literature every task. Save source metadata and brief permitted notes. Do not copy copyrighted papers into the public repository without rights. A link permits citation, not redistribution. A blocked model license requires a licensed alternative before the global reconstructed view can ship.

## M1-01 verified evidence ledger — 2026-09-12

Only primary scientific/official sources were promoted here. Search results and secondary pages were used only to locate primary material. No terrain, scene, model output, or application asset was created.

### Verified source metadata

| ID | Source metadata | Verification and precise locator | Rights status | Limitations |
|---|---|---|---|---|
| G07 | Graymer, R.W., Brabb, E.E., Jones, D.L., Barnes, J., Nicholson, R.S., and Stamski, R.E., 2007, *Geologic Map and Map Database of Eastern Sonoma and Western Napa Counties, California*, USGS Scientific Investigations Map 2956, version 1.0, DOI 10.3133/sim2956. Published map scale 1:100,000; derived from geologic-map databases containing information at 1:62,500-scale resolution. | **content_verified for map identity/scope and unit-description availability**. USGS SIM 2956 index page and publication record; pamphlet description-of-map-units section includes “Sonoma Volcanics (Pliocene and late Miocene)” and unit symbols such as Tsv and Tsr. | **allowed for USGS-produced report/map content in the U.S.**, with attribution; USGS states its authored/produced information is generally public domain. Any individually marked third-party material remains excluded unless separately cleared. | Suitable regional/local geologic baseline, but map scale limits interpretation. This verification does **not** yet prove which polygon contains the exact modern summit coordinate. |
| G08 | McLaughlin, R.J., Sarna-Wojcicki, A.M., Fleck, R.J., Wright, W.H., Levin, V.R.G., and Valin, Z.C., 2004, *Geology, Tephrochronology, Radiometric Ages, and Cross Sections of the Mark West Springs 7.5' Quadrangle, Sonoma and Napa Counties, California*, USGS Scientific Investigations Map 2858, scale 1:24,000, DOI 10.3133/sim2858. | **content_verified for mapped southwest Mount St. Helena/Franz Valley context**. Sheet 1 description states that on the southwest slope of Mt. St. Helena, andesite and basaltic andesite are intercalated in rhyodacite ash-flow tuff (Tst). Sheet 2 provides dated volcanic-rock localities and cross sections. | **allowed for USGS-produced report/map content in the U.S.**, with attribution; exclude any specifically marked third-party item. | Higher-resolution local context but the Mark West Springs quadrangle does not by itself establish the exact summit map unit. Do not extrapolate its southwest-slope Tst unit to the summit. |
| G09 | Sweetkind, D.S., Rytuba, J.J., Langenheim, V.E., and Fleck, R.J., 2011, *Geology and geochemistry of volcanic centers within the eastern half of the Sonoma volcanic field, northern San Francisco Bay region, California*, Geosphere 7(3):629–657, DOI 10.1130/GES00625.1. | **content_verified for Mount St. Helena volcanic-center claims**. General description p. 633; Table 2 pp. 636–637; “Mount St. Helena Volcanic Center” section p. 642. Authors define a Mount St. Helena center, place it at/near Mount St. Helena and Franz Valley, associate the 2.85 Ma tuff of Franz Valley with that center, interpret that eruption as caldera-forming, and report an intracaldera tuff age of 2.83 ± 0.08 Ma. | **evidence citation allowed; article/figure redistribution not admitted**. The article is an external Geosphere publication and the displayed copy carries Geological Society of America copyright/permission language. Do not package article pages, figures, or tables without explicit permission. | These dates concern volcanic products/events and an interpreted volcanic center. They do **not** date acquisition of the mountain’s present topographic form. Local reconstructive geometry remains unapproved. |
| G10 | Mankinen, E.A., 1972, *Paleomagnetism and potassium-argon ages of the Sonoma Volcanics, California*, GSA Bulletin 83(7):2063–2072, DOI 10.1130/0016-7606(1972)83[2063:PAPAOT]2.0.CO;2. | **content_verified only at abstract scope**. USGS Publications Warehouse abstract states that Gauss normal polarity is represented by rocks from Mount St. Helena and that dated Sonoma volcanic rocks range from 5.3 Ma to about 2.9 Ma. | **evidence citation allowed; redistribution unresolved/not admitted**. Journal article rights were not separately cleared. | Abstract does not establish that 5.3–about 2.9 Ma is the age of Mount St. Helena or its present landform. Do not use the field/sample range as a mountain lifetime. |
| G11 | U.S. Geological Survey, *1/3rd arc-second Digital Elevation Models (DEMs) — USGS National Map 3DEP Downloadable Data Collection*, Science Data Catalog record USGS:3a81321b-c153-416f-98b7-cc8e5f0e17c3. | **metadata/content_verified for collection characteristics and rights**. Catalog states ~10 m resolution, bare-earth elevations, geographic coordinates/NAD83, elevations in meters, NAVD88 over CONUS, and continually updated tiled GeoTIFF products. | **allowed / public domain**. Catalog explicitly states all 3DEP products are public domain and supplies the U.S. public-domain license label. | Collection-level verification only. No Mount St. Helena tile was fetched; exact tile date/source epoch, checksum, and local coverage remain unverified until an authorized data-preparation milestone. |
| G12 | Merdith, A., 2021, *Plate model for “Extending Full-Plate Tectonic Models into Deep Time: Linking the Neoproterozoic and the Phanerozoic”*, Zenodo record 4485738, DOI 10.5281/zenodo.4485738. | **metadata_verified**. Zenodo identifies the resource as a dataset/plate model for the last 1 Ga accompanying Merdith et al. (2021) and exposes file `SM2_4485738_V2.zip`. | **unresolved**. The current primary Zenodo record inspected for M1-01 does not expose an explicit license value in the retrieved metadata. Public download availability is not treated as redistribution permission. | Not admitted as a distributable project asset until explicit dataset rights/license and a pinned version/reference frame are verified. No local Mount St. Helena anchor may be derived from this global model. |

### M1-01 precise claim candidates

These are research-ledger candidates only; none is expert-reviewed or publication-approved.

| Claim ID | Candidate statement | Scope / class | Evidence locator | Limitations / disposition |
|---|---|---|---|---|
| M1C01 | Mount St. Helena is a named California locality within the northern California Coast Ranges and is explicitly treated in USGS geologic mapping of Sonoma/Napa County. | local / observed | G07 map coverage and G08 title/sheets; G08 sheet 1 explicitly labels “Mount St. Helena.” | **candidate supported for identity**. Exact authoritative summit coordinate/feature identifier has not been content-verified in this task; keep coordinate null. |
| M1C02 | USGS SIM 2956 is a suitable baseline geologic map for eastern Sonoma and western Napa Counties, published at 1:100,000 from databases containing information at about 1:62,500-scale resolution. | regional / observed | G07 USGS index/publication record. | **supported** for baseline selection only. Zooming cannot imply finer geologic certainty. |
| M1C03 | On the southwest slope of Mount St. Helena, SIM 2858 maps andesite/basaltic andesite intercalated with rhyodacite ash-flow tuff (Tst). | local / observed | G08 sheet 1, description of map units adjacent to mapped Mount St. Helena area. | **supported only for the southwest-slope area represented by that map**. Do not promote Tst as the summit unit. |
| M1C04 | Sweetkind et al. define a Mount St. Helena volcanic center located north and northwest of Calistoga, at and near Mount St. Helena and in the vicinity of Franz Valley. | local-regional / interpreted | G09 p. 633 and Table 2 pp. 636–637. | **supported** as the authors’ volcanic-center interpretation; not a recovered exact vent/caldera boundary for visualization without geometry review. |
| M1C05 | Sweetkind et al. interpret eruption of the 2.85 Ma tuff of Franz Valley as formation of the Mount St. Helena caldera. | local-regional / interpreted | G09 “Mount St. Helena Volcanic Center,” p. 642; Table 2 pp. 636–637. | **supported as an interpretation**. 2.85 Ma is an eruptive-event age, not the age of the modern mountain shape. No exact ancient topography follows from this claim. |
| M1C06 | Sweetkind et al. report intracaldera tuff associated with the Mount St. Helena caldera at 2.83 ± 0.08 Ma and correlate it with the tuff of Franz Valley. | local-regional / interpreted | G09 p. 642. | **supported**, preserving the published uncertainty. Does not establish when erosion/uplift produced the present summit profile. |
| M1C07 | The Sonoma Volcanics as a regional field span a broader interval than the Mount St. Helena event-specific dates; Wagner et al. summarize Sonoma Volcanics at about 8–2.5 Ma. | regional / interpreted | G02 USGS Publications Warehouse abstract. | **supported only at regional field scope**. Explicitly reject use as a summit eruption date or Mount St. Helena “age.” |
| M1C08 | Mankinen reports Sonoma volcanic rocks dated from 5.3 Ma to about 2.9 Ma and identifies Mount St. Helena rocks with the Gauss normal polarity epoch. | regional with local observation / observed+interpreted | G10 USGS Publications Warehouse abstract. | **supported only at abstract scope**. The 5.3–about 2.9 Ma range must not be assigned wholesale to Mount St. Helena. |
| M1C09 | The USGS 3DEP 1/3 arc-second DEM collection is an admissible candidate source for modern terrain because its collection metadata explicitly places the products in the public domain. | modern regional / observed metadata | G11 Science Data Catalog collection record. | **rights supported, asset not yet prepared**. Exact tile provenance/epoch remains a future requirement. |

### Required evidence gaps retained after M1-01

- **GAP-M1-01-A — exact modern summit anchor:** Mount St. Helena identity is verified from primary USGS mapping, but this task did not content-verify the authoritative GNIS summit feature identifier and coordinate. Do not populate `local_anchor` yet.
- **GAP-M1-01-B — summit map unit:** The exact polygon/map unit containing the modern summit has not been verified by coordinate-to-map/database intersection. The southwest-slope Tst observation in SIM 2858 must not be extrapolated to the summit.
- **GAP-M1-01-C — present landform age:** No reviewed source in this task dates when Mount St. Helena acquired its present topographic form. The 2.85 Ma and 2.83 ± 0.08 Ma claims date volcanic events/products, not modern morphology.
- **GAP-M1-01-D — local deep-time position:** No source supports tracking the modern summit or Napa locality backward through deep time. The 1 Ga global model, if later licensed, remains global context only with no local anchor.
- **GAP-M1-01-E — plate-model redistribution:** Zenodo record 4485738 is verified as the intended 1 Ga dataset record, but explicit redistribution rights were not verified from the primary record. Asset admission remains blocked.

## M1-02 blocker-resolution pass — 2026-09-12

This pass remained evidence-only. No terrain, scenes, code, plate outputs, or bulk geologic datasets were created or downloaded.

### Primary-source verification updates

| ID | Source metadata | Verification and precise locator | Rights status | Limitations / disposition |
|---|---|---|---|---|
| G13 | U.S. Geological Survey, The National Map Gazetteer / Geographic Names Information System (GNIS), `geonames` FeatureServer and MapServer. | **content_verified for service authority, schema, coordinate reference, and update status**. The primary USGS service states that the Gazetteer is the federal and national standard for geographic nomenclature based on GNIS; the Landform layer exposes `gaz_name`, `gaz_featureclass`, `state_alpha`, `county_name`, and permanent `gaz_id`; service spatial reference is EPSG:4326; data were refreshed July 2026. | **allowed / public domain**. The USGS service states that The National Map download client provides free downloads of public-domain geographic-names data. | The service itself is authoritative, but this pass did not retrieve the specific Mount Saint Helena feature row from the primary query endpoint. Therefore feature ID 232163 and coordinate 38.66935, -122.63332 remain **withheld from the project anchor** rather than promoted from secondary mirrors. |
| G07-update | Graymer et al. (2007), USGS SIM 2956, direct standard-resolution map PDF `sim2956f.pdf` and USGS index page. | **content_verified for the actual map sheet and database availability**. The full primary map sheet was inspected; the USGS index confirms the Digital Database Package contains the geologic map database and supporting data. | **allowed for USGS-produced map/database material in the U.S.**, subject to any individually marked third-party content. | The map sheet inspection did not provide a defensible point-in-polygon determination at the modern summit coordinate. The 57.7 MB digital database package was not downloaded because the current operating contract forbids bulk data acquisition. The exact summit unit therefore remains a gap. |
| G12-update | Zenodo record 4485738 plus current Zenodo licensing documentation. | **metadata_verified for the exact Merdith dataset record; platform policy content_verified**. Zenodo currently requires a license field for deposited records and defaults to CC BY 4.0, but the current primary rendering of record 4485738 still exposes no explicit license value tied to the record/file. | **unresolved for redistribution**. Platform defaults are not substituted for an explicit asset-specific rights statement. | Secondary evidence that the animation was once available under CC BY 4.0 was deliberately not used to admit the model because M1 requires primary rights verification for the exact redistributed asset. |
| G14 | Cao et al. (2024), *Earth's tectonic and plate boundary evolution over 1.8 billion years*, Zenodo record 13628813, version 2.4, DOI 10.5281/zenodo.13628813. | **metadata_verified as a possible >1 Ga alternative model**. The primary Zenodo record identifies a full-plate reconstruction from 1.8 Ga to present and a 20.7 MB model archive. | **unresolved**. The primary record's rendered Rights section also does not expose a license value. | Rejected as a rights-resolution substitute for M1 at this time. It does not solve E04 merely by being newer or openly downloadable. |

### M1-02 precise claim dispositions

| Claim ID | Candidate statement | Scope / class | Evidence locator | Limitations / disposition |
|---|---|---|---|---|
| M1C10 | The USGS National Map Gazetteer is the authoritative federal geographic-names service suitable for establishing the modern Mount Saint Helena anchor, and its landform data use EPSG:4326 with permanent feature IDs. | modern/local metadata / observed | G13 USGS `geonames` FeatureServer service description, Landform layer field list, and service spatial-reference metadata. | **supported as source-selection metadata**. It does not by itself prove the specific Mount Saint Helena ID/coordinate until the primary feature row is retrieved. |
| M1C11 | Mount Saint Helena has GNIS/USGS feature ID 232163 at 38.66935 N, -122.63332 W. | modern/local / observed | Primary feature-row retrieval not completed. | **WITHHELD / GAP**. Secondary mirrors agree, but the project requires a primary authoritative record before populating `local_anchor`. |
| M1C12 | The exact modern summit lies in a specific SIM 2956 geologic-map unit. | modern/local / observed | G07 primary map sheet inspected; no point-in-polygon/database query completed. | **WITHHELD / GAP**. Do not promote `Tst`, `Tswt`, or another unit by visual inference or southwest-slope extrapolation. |
| M1C13 | The Merdith 1 Ga plate-model files may be redistributed under CC BY 4.0. | global / rights metadata | G12 exact Zenodo record plus Zenodo licensing policy. | **WITHHELD / GAP**. Current primary record does not expose an explicit asset-specific license value, so redistribution remains unresolved under E04. |

### M1-02 gap disposition

- **GAP-M1-01-A retained:** authoritative service is identified and verified, but the specific primary Mount Saint Helena feature row was not retrieved. Keep `local_anchor` unset.
- **GAP-M1-01-B retained:** actual SIM 2956 map sheet is verified, but exact summit polygon/unit remains unresolved. No visual inference is admitted.
- **GAP-M1-01-C retained:** no source reviewed here dates acquisition of the present topographic form.
- **GAP-M1-01-D retained:** no ancient local position is admitted.
- **GAP-M1-01-E retained:** neither Merdith 2021 nor the evaluated Cao et al. 2024 alternative has an explicit license value exposed in the primary Zenodo record rendering used here; global model asset admission remains blocked.

## M1-03 official-feature and summit-intersection check — 2026-09-12

Only the two requested checks were attempted. No terrain, scenes, plate-model output, or application code was created. One live route and one official alternative were attempted for GNIS; one original-database route and the official NGMDB alternative were attempted for the geologic intersection. Failed routes were not repeated.

### G15 — GNIS official feature-route verification
- **Primary source:** U.S. Geological Survey / U.S. Board on Geographic Names, *Download GNIS Data* and GNIS Domestic Names Search Application.
- **Official routes discovered:** live Domestic Names Search Application; The National Map Staged Products Directory for state DomesticNames/FullModel downloads; The National Map `geonames` MapServer.
- **Service discovery:** the official National Map service directory exposes `geonames`; its `Landforms` layer is ID 5 and exposes `gaz_id`, `gaz_name`, `gaz_featureclass`, `state_alpha`, `county_name`, and geometry fields. The layer links to its own official Query operation. Service metadata states the data were refreshed July 2026.
- **File-format authority:** USGS *GNIS Data Products — File Format Documentation*, dated 2025-11-13, defines `feature_id` as the permanent unique feature identifier, `feature_name` as the official feature name, `feature_class`, state/county attributes, and primary coordinates as the **official feature location** in **NAD83**. Decimal fields carry seven decimal places in the product specification; this stored precision is not asserted as positional accuracy.
- **Feature-point semantics:** the checked official documentation does **not** state that a mountain's primary coordinate is necessarily its highest summit or a particular peak. Therefore any future retrieved coordinate must be called the **GNIS feature point** unless a separate authoritative source establishes exact-summit meaning.
- **Query/filter attempted:** California; Mount Saint Helena / Mount St. Helena spelling variants. The JavaScript live search could not be executed in this environment; the documented REST query form was discovered, but arbitrary query parameters could not be submitted by the available browser. The official staged-download alternative was then inspected, but the specific current California file target was not exposed/downloadable in this environment.
- **Disposition:** **PARTIAL / GAP for record values.** The authoritative system, route, schema, CRS, and semantics are verified. The official feature row itself was not retrieved, so official feature name, feature ID, feature class, county attributes, and primary coordinates remain withheld from the project anchor.
- **Evidence file:** `M1_GNIS_CHECK_2026-09-12.txt`; SHA-256 `8ca356f87798b43d8071a0a95cee3c8045e3cf21cb50899d90a1b534b7f51da1`.

### G07-update-2 — SIM 2956 GIS intersection attempt
- **NGMDB discovery:** NGMDB product 81179 identifies Graymer et al. (2007), USGS SIM 2956, scale 1:100,000, and states that the publication includes the original ARC/INFO 7.x GIS data plus an NGMDB shapefile conversion made in February 2024.
- **Original USGS publication:** Graymer, R.W., Brabb, E.E., Jones, D.L., Barnes, J., Nicholson, R.S., and Stamski, R.E., 2007, *Geologic Map and Map Database of Eastern Sonoma and Western Napa Counties, California*, USGS Scientific Investigations Map 2956, version 1.0, DOI 10.3133/sim2956.
- **Nominal scale / database resolution:** published map 1:100,000; derived from geologic map databases containing information at approximately 1:62,500-scale resolution.
- **Geologic polygon coverage:** the publication identifies `eswn-geol.e00` / `eswn-geol/` as the polygon-and-line coverage containing faults, depositional contacts, and rock units.
- **Official GIS acquisition attempt:** the original `sim2956c.tgz` Digital Database Package was identified (57.7 MB compressed) but could not be retrieved through the available download route. The NGMDB product page was the official alternative; it confirms the converted shapefile exists but direct retrieval was access-blocked in this environment.
- **Intersection status:** **GAP.** Because no authoritative GIS polygon dataset was successfully acquired, no coordinate transformation, point-to-polygon intersection, polygon identifier, unit symbol, unit name, lithology, published age designation, contact proximity, overlap, or no-data test was performed. No nearest polygon was substituted and no map-image interpretation was promoted.
- **Evidence file:** `M1_GEOLOGY_INTERSECTION_CHECK_2026-09-12.txt`; SHA-256 `881deee4cdecde628d59958829f86fbab39ac29a38e25b1131fe05d63d143f50`.

### Status separation after M1-03
- **Identity:** VERIFIED at the level that Mount St. Helena / Mount Saint Helena, California is the intended named geographic feature in authoritative USGS mapping/GNIS context; the exact official GNIS row remains unexported in this pass.
- **Exact-summit position:** **GAP.** No checked GNIS source establishes that its primary feature point is the highest summit, and the official feature row was not retrieved.
- **Mapped-unit intersection:** **GAP.** No authoritative GIS point-in-polygon result exists yet.
- **Landform age:** **GAP retained.** No source in these checks dates development of the modern topographic landform; volcanic-product/event ages remain separate.

## M1-04 global plate-model rights recheck — 2026-09-12

This bounded pass addressed only the next unblocked M1 source-rights item. No model files were downloaded, no reconstruction was run, and no scene or terrain asset was created.

### G12-update-2 — Merdith 1 Ga model
- Primary record: Andrew Merdith, 2020/2021, *Plate model for 'Extending Full-Plate Tectonic Models into Deep Time: Linking the Neoproterozoic and the Phanerozoic'*, Zenodo record 4485738, DOI 10.5281/zenodo.4485738.
- Verified version: 1.1b, published 2020-12-16; resource type Dataset; publisher Zenodo.
- Verified file: `SM2_4485738_V2.zip`, displayed size 13.9 MB, MD5 `170dc478bec01dacfeba6a253fb76351`.
- Verified scope: Zenodo describes it as the plate model for the last 1 Ga accompanying Merdith et al. (2021). EarthByte describes the model as a first-step, geologically constrained full-plate reconstruction in a paleomagnetic reference frame and provides the model files for community use.
- Rights check: the current Zenodo record renders a Rights section with a License label but no license value. A search within the primary record returned no CC BY text.
- Disposition: **redistribution rights unresolved**. "Open" access and community-download language are not substituted for an explicit asset-specific redistribution license under the project evidence rules. Do not package the model or derived model assets until rights are explicit or a clearly licensed alternative is selected.
- Limitation: even if later licensed, this model supports globe-scale plate context only. It does not establish the ancient position of the modern Mount St. Helena feature point, parcel, coastline, or topography.

### M1-04 claim/right disposition
- M1C13 remains **WITHHELD / GAP**: the statement that the Merdith 1 Ga files may be redistributed under CC BY 4.0 is not supported by the exact primary record currently rendered.
- GAP-M1-01-E remains open: global plate-model asset admission is blocked on explicit redistribution terms.

## M1-05 GNIS export + original SIM 2956 GIS processing — 2026-09-12

### G15-update — official Mount Saint Helena feature record
- **Evidence:** user-exported official USGS GNIS feature-detail PDF, `Mount Saint Helena USGS.pdf`, SHA-256 `19a305ee5cb88481d602880e47206835eeb803c1572e7289262122e654026d4a`.
- **content_verified:** official name **Mount Saint Helena**; Feature ID **232163**; Class/Feature Code **Summit**; Primary State **California**; Primary County **Sonoma County**; Primary Map **Mount Saint Helena**; coordinate **38.6691784, -122.6333914** (38°40'09.04" N, 122°38'00.21" W); Landform Point Type **High Point**.
- GNIS product documentation previously verified that primary coordinates are NAD83. Preserve the source decimal precision but do not present it as positional accuracy.
- **Disposition:** GAP-M1-01-A is resolved for the authoritative GNIS feature point and GNIS `High Point` designation. The GNIS designation is not independently reinterpreted as a survey proof of the absolute highest elevation.

### G07-update-3 — original SIM 2956 GIS package acquired and processed
- **Original USGS package:** `sim2956c.tgz`, SHA-256 `3d2feff64c8fa5448694dc9b858657ec267afc37144f009304aa0de4e5d2588e`.
- **Geologic coverage:** `eswngeo/eswn-geol.e00`, SHA-256 `ccab4021858cef659d7a3d3c1b26d02ed127811171477fbead074d557c881df3`.
- Embedded E00 PRJ states **UTM, Zone 10, meters, Clarke 1866**. FGDC metadata states **NAD27 / Clarke 1866**, but inconsistently labels the planar grid as State Plane zone 3326. Actual processing therefore used the embedded E00 UTM definition plus the metadata datum: **NAD27 / UTM zone 10N (EPSG:26710)**. Preserve the metadata inconsistency as a source limitation.
- E00 topology was parsed deterministically: 10,324 arcs; polygonization yielded 4,003 mapped polygon faces. The GNIS point was transformed from NAD83 to EPSG:26710 using locally available PROJ. The installation lacked the preferred NADCON transformation grid, so PROJ used its documented ballpark NAD83-to-NAD27 geographic offset before UTM projection. Processing coordinate: **E 531985.8215061416 m, N 4279937.239342171 m**.
- Exactly one polygon face covered that processing point. It contains E00 label record **ID 636 / polygon 584**. `ESWN-GEOL.PAT` polygon 584 / ID 636 has original `PTYPE` **Tswt**.
- **Published unit description:** `Tswt` — **Welded ash-flow tuff**; also includes minor partly welded and unwelded ash-flow tuff. The unit is listed within **Sonoma Volcanics (Pliocene and late Miocene)**.
- **Do not assign the pamphlet's broad Sonoma Volcanics field range (2.6 ± 0.3 to 8.24 ± 0.22 Ma) to this polygon or to Mount Saint Helena.** No specific radiometric age for polygon 584 was established by this intersection.
- Under the same processing transform, the nearest mapped boundary is E00 arc **1335**, approximately **335.7435 m** away in coverage coordinates. Its AAT record is `contact, certain`, separating polygon 584 `Tswt` from polygon 493 `Tslt`. SIM 2956 metadata defines `contact, certain` as observed/closely constrained and well-located; well-located items are intended within 0.5 mm at 1:62,500 (~31 m on the ground), with additional base-map inaccuracies possible.
- No overlap or no-data condition was encountered at the processing point.
- **Disposition:** the deterministic available transformation yields **Tswt**, but the mapped-unit check remains **PARTIAL rather than fully VERIFIED** until a high-accuracy NAD83-to-NAD27 transformation is run with the required NADCON grid/service. No uncertainty radius is invented. The result applies only to the mapped unit at the GNIS point and does not characterize the entire mountain or subsurface.
- **Processing evidence:** `M1_GNIS_SIM2956_INTERSECTION_2026-09-12.txt`, SHA-256 `7711aead47ab617fa4f2c476fb00c6be573683d4bf54044b635d66e25e4028c0`.

### M1-05 status separation
- **Identity:** VERIFIED.
- **Official GNIS feature point:** VERIFIED — Feature ID 232163, NAD83 coordinate retained at source precision.
- **GNIS high-point designation:** VERIFIED as the record's Landform Point Type.
- **Mapped-unit intersection:** PARTIAL — deterministic result `Tswt`; final datum-transform verification pending.
- **Mapped-unit age:** only published designation **Pliocene and late Miocene** via the Sonoma Volcanics unit hierarchy; no polygon-specific numeric age established.
- **Modern landform age:** GAP retained.

## M1-06 authoritative datum-transform verification attempt — 2026-09-12

### G16 — NOAA NGS NCAT/NADCON verification route
- **Primary source:** NOAA National Geodetic Survey, Coordinate Conversion and Transformation Tool (NCAT) API documentation. NCAT states that it uses NADCON 5.0 for latitude/longitude/ellipsoid-height transformations and supports CONUS transformations among NAD27, NAD83(1986), NAD83(HARN), NAD83(FBN), NAD83(NSRS2007), and NAD83(2011).
- **Input evidence:** official GNIS Mount Saint Helena point 38.6691784, -122.6333914. GNIS documentation identifies the datum generically as NAD83 but the retrieved feature record does not specify the NAD83 realization.
- **Attempted operation:** authoritative NAD83-to-NAD27 transformation through the documented NCAT latitude-longitude service, with UTM zone 10 requested for comparison to SIM 2956. Direct API execution was not reachable from the available runtime/network. The local PROJ database identifies the preferred NADCON 5 grid `us_noaa_nadcon5_nad27_nad83_1986_conus.tif` (EPSG operation 8555, stated 0.15 m accuracy) but that grid is not installed locally; the official PROJ CDN entry was discovered but binary retrieval failed in this runtime.
- **Disposition:** **PARTIAL / transformation gap retained.** Do not guess the GNIS NAD83 realization and do not upgrade the Tswt intersection to fully VERIFIED from the ballpark transform alone.
- **Important robustness note:** the current deterministic intersection remains Tswt and the nearest mapped contact under the same processing transform is ~335.7 m away, but no quantitative uncertainty radius is inferred from that fact.
