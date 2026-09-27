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
    return {"properties": {"ava_id": ava_id, "name": ava_id, "within": within, "valid_end": valid_end,
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

    def test_napa_frame_rectangular_and_covers_ava(self):
        r = self.load("napa_valley.json")
        w, h, nx, ny = region_request(r)
        self.assertEqual((w, h), (1843, 2400))
        self.assertEqual(ny, 512)
        self.assertEqual(nx, round(512 * 1843 / 2400))
        with open(os.path.join(ROOT, "prototype", "assets", "ava.json")) as f:
            napa = json.load(f)["avas"][0]
        self.assertEqual(napa["id"], "napa_valley")
        x0, y0, x1, y1 = r["bbox_utm"]
        for ring in napa["rings"]:
            for x, y in ring:
                self.assertTrue(x0 <= x * 1000 <= x1 and y0 <= y * 1000 <= y1)


if __name__ == "__main__":
    unittest.main()
