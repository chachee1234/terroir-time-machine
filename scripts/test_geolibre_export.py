import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geolibre_export as gx  # noqa: E402

REQUIRED = ("version", "name", "mapView")   # what GeoLibre's parseProject rejects a project without


class GeoLibreExportTest(unittest.TestCase):
    def test_faults_parse_every_row_of_the_viewer_table(self):
        html = gx.VIEWER.read_text()
        rows = len(re.findall(r'^ \{n:"', re.search(r"const FAULTS=\[(.*?)\n\];", html, re.S).group(1), re.M))
        faults = gx.viewer_faults(html)
        self.assertEqual(len(faults), rows)
        self.assertGreaterEqual(rows, 10)
        for f in faults:   # all traces sit in the North Coast ranges around Napa
            for lon, lat in f["geometry"]["coordinates"]:
                self.assertTrue(-123.2 < lon < -121.8 and 37.9 < lat < 39.3, (f["properties"]["name"], lon, lat))
        self.assertEqual({f["properties"]["kind"] for f in faults}, {"strike-slip", "thrust"})

    def test_scene_origin_maps_to_the_gnis_summit(self):
        html = 'const GNIS_UTM=[531892.63,4280129.75];\nconst FAULTS=[\n {n:"T", r:"x", pts:[[0,0],[1,0]]}\n];'
        (lon, lat), (lon1, _) = gx.viewer_faults(html)[0]["geometry"]["coordinates"]
        self.assertAlmostEqual(lat, 38.6694, places=3)
        self.assertAlmostEqual(lon, -122.6333, places=3)
        self.assertGreater(lon1, lon)   # +x is east

    def test_mapped_region_project(self):
        p = gx.project("napa_valley", gx.viewer_faults())
        for k in REQUIRED:
            self.assertIn(k, p)
        ids = [l["id"] for l in p["layers"]]
        self.assertEqual(ids, ["ttm-napa_valley-frame", "ttm-napa_valley-ava", "ttm-napa_valley-subavas",
                               "ttm-napa_valley-faults"])
        self.assertEqual(p["metadata"]["status"], "mapped")
        x0, y0, x1, y1 = p["mapView"]["bbox"]
        self.assertTrue(x0 < p["mapView"]["center"][0] < x1 and y0 < p["mapView"]["center"][1] < y1)
        for l in p["layers"]:
            self.assertEqual(l["type"], "geojson")
            self.assertEqual(l["geojson"]["type"], "FeatureCollection")
            self.assertTrue(l["geojson"]["features"])

    def test_planned_region_has_no_frame_and_cites_sources(self):
        p = gx.project("sonoma_valley", gx.viewer_faults())
        self.assertEqual(p["metadata"]["status"], "planned")
        self.assertNotIn("ttm-sonoma_valley-frame", [l["id"] for l in p["layers"]])
        self.assertTrue(any("CC BY-SA" in s for s in p["metadata"]["sources"]))
        ring = p["layers"][0]["geojson"]["features"][0]["geometry"]["coordinates"][0]
        self.assertEqual(ring[0], ring[-1])   # closed ring

    def test_committed_files_match_the_index(self):
        idx = json.loads((gx.OUT / "index.json").read_text())
        for rid in idx["regions"]:
            p = json.loads((gx.OUT / f"{rid}.geolibre.json").read_text())
            self.assertEqual(p["metadata"]["region"], rid)
        self.assertIn("{id}", idx["open"])


if __name__ == "__main__":
    unittest.main()
