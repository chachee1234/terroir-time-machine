import json
import os
import unittest

from region_faults import select, triple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def trace(cid, pts, rate="(1.0,0.5,2.0)"):
    return {"type": "Feature", "geometry": {"type": "LineString", "coordinates": pts},
            "properties": {"catalog_id": cid, "name": cid + " 2011 CFM", "catalog_name": "UCERF3",
                           "slip_type": "Dextral", "average_dip": "(90,,)", "net_slip_rate": rate}}


class RegionFaultTests(unittest.TestCase):
    def test_triple_keeps_empty_slots(self):
        self.assertEqual(triple("(90,,)"), [90.0, None, None])
        self.assertEqual(triple("(17.96,13.2,22.88)"), [17.96, 13.2, 22.88])
        self.assertIsNone(triple(None))

    def test_keeps_traces_touching_frame_whole_and_drops_others(self):
        frame = [491100.0, 4215600.0, 551700.0, 4249200.0]
        inside = trace("A", [[-122.6, 38.2], [-122.9, 38.6]])      # starts inside, leaves the frame
        outside = trace("B", [[-121.0, 37.0], [-121.1, 37.1]])
        got = select([outside, inside], frame)
        self.assertEqual([q["id"] for q in got], ["A"])
        self.assertEqual(len(got[0]["pts_km"]), 2)
        self.assertEqual(got[0]["label"], "A")
        self.assertEqual(got[0]["dip_deg"], 90.0)

    def test_petaluma_gap_file_matches_its_frame(self):
        self.check_frame("petaluma_gap")

    def test_northern_sonoma_file_matches_its_frame(self):
        self.check_frame("northern_sonoma")

    def test_west_sonoma_coast_file_matches_its_frame(self):
        self.check_frame("west_sonoma_coast")

    def test_mendocino_file_matches_its_frame(self):
        self.check_frame("mendocino")

    def check_frame(self, rid):
        with open(os.path.join(ROOT, "data", "regions", rid + ".json")) as f:
            r = json.load(f)
        with open(os.path.join(ROOT, r["assets_dir"], "faults.json")) as f:
            d = json.load(f)
        x0, y0, x1, y1 = [v / 1000 for v in r["bbox_utm"]]
        self.assertTrue(d["faults"])
        for q in d["faults"]:
            self.assertTrue(any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in q["pts_km"]), q["id"])


if __name__ == "__main__":
    unittest.main()
