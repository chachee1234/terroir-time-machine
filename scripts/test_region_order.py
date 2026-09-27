import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import region_order as ro  # noqa: E402


def box(i, name, x0, y0, x1, y1, within=None):
    return {"id": i, "name": name, "within": within, "rings": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


class RegionOrderTest(unittest.TestCase):
    def setUp(self):
        d = 0.1  # degrees, about 9-11 km
        avas = [box("napa", "Napa", 0, 0, d, d), box("sonoma", "Sonoma", -d, 0, 0, d),
                box("inner", "Inner", -0.08, 0.02, -0.02, 0.08, "Sonoma"),
                box("west", "West", -2 * d, 0, -d, d), box("far", "Far", 1.0, 1.0, 1.0 + d, 1.0 + d),
                box("near", "Near", 0.3, 0, 0.3 + d, d), box("huge", "Huge", -3, -3, 3, 3)]
        self.tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump({"avas": avas}, self.tmp); self.tmp.close()
        self.avas = ro.load(self.tmp.name)

    def test_order_follows_the_owner_rule(self):
        seq = ro.order(self.avas, "sonoma", ["napa"])
        self.assertEqual([s["id"] for s in seq], ["sonoma", "west", "near", "far"])
        self.assertEqual(seq[0]["rule"], "owner's choice")
        self.assertEqual(seq[1]["rule"], "touches a mapped region")
        self.assertEqual(seq[2]["rule"], "closest (nothing touching)")
        self.assertIn("inner", seq[0]["close_ups"])       # nested AVAs become close-ups, not regions
        self.assertNotIn("huge", [s["id"] for s in seq])  # umbrella AVAs are too big for one frame


if __name__ == "__main__":
    unittest.main()
