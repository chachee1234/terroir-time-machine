"""Tier 0 tests for the AVA extractor and region requests. Runs under pytest or unittest."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from ava_extract import select, simplify  # noqa: E402
from fetch_terrain import region_request  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def feat(ava_id, within, valid_end=None):
    return {"properties": {"ava_id": ava_id, "name": ava_id.replace("_", " ").title(), "within": within, "valid_end": valid_end,
                           "created": "2000-01-01", "cfr_index": "9.0"}, "geometry": {"type": "Polygon", "coordinates": []}}


class SelectTests(unittest.TestCase):
    def test_parent_first_nested_kept_others_dropped(self):
        got = select([feat("rutherford", "Napa Valley|North Coast"), feat("sonoma_valley", "North Coast|Sonoma Coast"),
                      feat("napa_valley", "North Coast"), feat("oakville", "Napa Valley|North Coast")])
        self.assertEqual([f["properties"]["ava_id"] for f in got], ["napa_valley", "oakville", "rutherford"])

    def test_superseded_versions_dropped(self):
        got = select([feat("napa_valley", "North Coast"), feat("calistoga", "Napa Valley", valid_end="2011-01-01")])
        self.assertEqual([f["properties"]["ava_id"] for f in got], ["napa_valley"])

    def test_substring_is_not_membership(self):
        self.assertEqual(select([feat("x", "Napa Valley East|North Coast")]), [])


class SimplifyTests(unittest.TestCase):
    def test_collinear_points_removed(self):
        self.assertEqual(simplify([(0, 0), (1, 0.001), (2, 0), (3, 0)], 0.01), [(0, 0), (3, 0)])

    def test_corner_kept(self):
        self.assertEqual(simplify([(0, 0), (5, 5), (10, 0)], 0.5), [(0, 0), (5, 5), (10, 0)])


class RegionTests(unittest.TestCase):
    def load(self, name):
        with open(os.path.join(ROOT, "data", "regions", name)) as f:
            return json.load(f)

    def test_current_block_is_square_224(self):
        self.assertEqual(region_request(self.load("mt_st_helena.json")), (1000, 1000, 224, 224))

    def test_napa_sonoma_frame_covers_every_ava_it_lists(self):
        r = self.load("napa_valley.json")
        w, h, nx, ny = region_request(r)
        self.assertEqual((w, h), (2540, 2550))
        self.assertEqual(ny, 548)
        self.assertEqual(nx, round(548 * 2540 / 2550))
        with open(os.path.join(ROOT, "prototype", "assets", "ava.json")) as f:
            avas = json.load(f)["avas"]
        self.assertEqual([a["id"] for a in avas if a.get("parent")], ["napa_valley", "sonoma_valley"])
        self.assertEqual(r["parents"], ["napa_valley", "sonoma_valley"])
        x0, y0, x1, y1 = r["bbox_utm"]
        for a in avas:
            for ring in a["rings"]:
                for x, y in ring:
                    self.assertTrue(x0 <= x * 1000 <= x1 and y0 <= y * 1000 <= y1, a["id"])

    def test_petaluma_gap_frame_has_its_own_outline_file(self):
        r = self.load("petaluma_gap.json")
        self.assertEqual(r["utm_zone"], 10)
        self.assertNotEqual(r["ava_viewer"], "prototype/assets/ava.json")   # never overwrites the Napa outlines
        with open(os.path.join(ROOT, r["ava_viewer"])) as f:
            v = json.load(f)
        self.assertEqual(v["region"], "petaluma_gap")
        self.assertEqual([a["id"] for a in v["avas"] if a.get("parent")], ["petaluma_gap"])
        x0, y0, x1, y1 = r["bbox_utm"]
        ax, ay = r["anchor"]["utm"]
        self.assertTrue(x0 < ax < x1 and y0 < ay < y1)
        for a in v["avas"]:
            for ring in a["rings"]:
                for x, y in ring:
                    self.assertTrue(x0 <= x * 1000 <= x1 and y0 <= y * 1000 <= y1, a["id"])

    def test_frame_rule_adds_avas_wholly_inside_and_drops_partial_ones(self):
        def sq(ava_id, within, lon0, lat0, d=0.05):
            f = feat(ava_id, within)
            f["geometry"]["coordinates"] = [[[lon0, lat0], [lon0 + d, lat0], [lon0 + d, lat0 + d], [lon0, lat0 + d], [lon0, lat0]]]
            return f
        frame = [507900.0, 4216800.0, 584100.0, 4293300.0]
        got = select([sq("napa_valley", "North Coast", -122.5, 38.3), sq("sonoma_valley", "North Coast", -122.55, 38.3),
                      sq("bennett_valley", "Sonoma Valley", -122.63, 38.38), sq("fountaingrove_district", "North Coast", -122.7, 38.5),
                      sq("russian_river_valley", "Northern Sonoma", -123.0, 38.4, 0.3)],
                     ("napa_valley", "sonoma_valley"), frame)
        self.assertEqual([f["properties"]["ava_id"] for f in got],
                         ["napa_valley", "sonoma_valley", "bennett_valley", "fountaingrove_district"])


if __name__ == "__main__":
    unittest.main()
