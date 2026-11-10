"""Tests for scripts/make_quaternary_texture.py and its committed output (offline)."""
import json
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_quaternary_texture as mq  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DETAIL = ROOT / "prototype/assets/regions/napa_valley/detail"


def polygon_shp(rings):
    """A one-record Polygon shapefile."""
    pts = [p for r in rings for p in r]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    body = struct.pack("<i4d2i", 5, min(xs), min(ys), max(xs), max(ys), len(rings), len(pts))
    k = 0
    for r in rings:
        body += struct.pack("<i", k)
        k += len(r)
    body += b"".join(struct.pack("<2d", *p) for p in pts)
    rec = struct.pack(">ii", 1, len(body) // 2) + body
    head = struct.pack(">i", 9994) + b"\0" * 20 + struct.pack(">i", (100 + len(rec)) // 2) + struct.pack("<ii", 1000, 5) + b"\0" * 64
    return head + rec


class Helpers(unittest.TestCase):
    def test_reads_polygon_with_hole(self):
        outer = [(0, 0), (0, 4), (4, 4), (4, 0), (0, 0)]
        hole = [(1, 1), (3, 1), (3, 3), (1, 3), (1, 1)]
        (bbox, rings), = mq.read_polygons(polygon_shp([outer, hole]))
        self.assertEqual(bbox, (0, 0, 4, 4))
        self.assertEqual(len(rings), 2)
        grid = [[None] * 5 for _ in range(5)]   # grid points 0..4 m, row 0 at y = 4
        mq.fill_rings(grid, rings, "Qhf", 0.0, 4.0, 1.0, 1.0, 5, 5)
        self.assertEqual(grid[2][2], None)       # (2, 2) is in the hole
        self.assertEqual(grid[2][0], "Qhf")      # (0, 2) on the outer west edge, inside

    def test_unit_names(self):
        meta = ("Attribute_Label: PTYPE\n Enumerated_Domain:\n  Enumerated_Domain_Value: Qhf\n"
                "  Enumerated_Domain_Value_Definition: Holocene alluvial fan deposits\nAttribute_Label: LIQ\n"
                "  Enumerated_Domain_Value: H\n  Enumerated_Domain_Value_Definition: High\n")
        self.assertEqual(mq.unit_names(meta), {"Qhf": "Holocene alluvial fan deposits"})


class Output(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads((DETAIL / "geology.json").read_text())

    def test_fine_map_recorded(self):
        f = self.d["fine"]
        self.assertIn("2006-1037", f["source"])
        self.assertEqual(len(f["input"]["sha256"]), 64)
        self.assertEqual(f["fallback"], ["br"])

    def test_corison_is_on_a_holocene_fan(self):
        c = next(q for q in self.d["closeups"] if q["id"] == "corison")
        self.assertGreater(c["fine_fraction"], 0.5)
        top = c["units"][0]
        self.assertEqual(top["ptype"], "Qhf")
        self.assertIn("24k", top["maps"])

    def test_units_and_pngs_agree(self):
        for q in self.d["closeups"]:
            self.assertTrue((DETAIL / q["file"]).exists(), q["id"])
            self.assertLessEqual(q["fine_fraction"], q["mapped_fraction"], q["id"])
            self.assertLessEqual(sum(u["cells"] for u in q["units"]), q["cols"] * q["rows"], q["id"])
            for u in q["units"]:
                self.assertTrue(set(u["maps"]) <= {"24k", "100k"}, q["id"])
                self.assertNotIn(u["ptype"], ("br", "H2O"), q["id"])


if __name__ == "__main__":
    unittest.main()
