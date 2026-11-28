# 2026-11-23 · region-stories · E1a parent material; E2 blocked

**Working branch:** `region-stories` (created from main at 6755c86, after PR #61 merged).

**E1a (done):** `scripts/ssurgo_layers.py` now reads each component's parent material (`copmgrp.pmgroupname`) and landform (`cogeomordesc.geomfname`) from Soil Data Access. Each component gets `parent_material`, `parent_class` and `landform` in `soils.json`. `parent_class` groups the survey's words into six classes: alluvium and colluvium; loess and eolian sand; volcanic rock and ash; sedimentary rock; serpentinite and ultramafic rock; igneous, metamorphic or residual bedrock. A name is classed by the material it names first, and "residuum weathered from X" by X.
- Fixture rows are recorded from Soil Data Access for mukey 458994 (Pleasanton). The cokey values in the fixtures are placeholders; the text is real.
- Napa rebuilt with `python3 scripts/ssurgo_layers.py --frame data/regions/napa_valley.json`: 396 map units, 95 soil names, 71.4 % of the frame covered (unchanged). Component classes in the file: sedimentary rock 198, alluvium and colluvium 183, volcanic rock and ash 92, igneous/metamorphic/residual bedrock 54, serpentinite and ultramafic rock 22, none 1032. Many components have no parent-material record in SDA or a name that matches no keyword; they stay `null`.
- Checks: SSURGO tests 13/13 (2 new: class grouping, parsed fields); full unit suite 217 tests OK (2 skipped); validate PASS; compileall OK; security_check OK; JS lint 17 scripts parse.

**E1b (next):** the viewer part, the "Formed in" line, the tour summary and the fourth colouring. The data is ready.

**E2 (blocked, owner decision):** the SGMC report (USGS Data Series 1052, `https://pubs.usgs.gov/ds/1052/ds1052.pdf`, p. ii) says the product "for the most part, is in the public domain, it also may contain copyrighted materials as noted in the text. Permission to reproduce copyrighted items must be secured from the copyright owner." That does not clear the licence for a statewide source. `mrdata.usgs.gov` (the data host) is not reachable from this sandbox, so the download URL was not checked. Choices for the owner: accept SGMC with a per-source copyright check (the report's text names the copyrighted items), or name another source. No substitute was used.

**Next action:** E1b (viewer). Owner: E2 decision.
