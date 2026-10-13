"""Tests for scripts/ssurgo_layers.py (offline)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ssurgo_layers as sl  # noqa: E402

# two Soil Data Access rows as they come back: one map unit, one component, two layers
ROWS = [
    ["458994", "170", "Pleasanton loam, 0 to 2 percent slopes, MLRA 14", "CA055", "Napa County, California", "9/16/2026 12:00:00 AM",
     "1", "Pleasanton", "85", "Yes", "Series", "Well drained", "Fine-loamy, mixed, superactive, thermic Mollic Haploxeralfs",
     "11", "Ap", "0", "13", "40", "40", "20", "0.75", "6.5", "0.17", "8.46", "5", "Loam"],
    ["458994", "170", "Pleasanton loam, 0 to 2 percent slopes, MLRA 14", "CA055", "Napa County, California", "9/16/2026 12:00:00 AM",
     "1", "Pleasanton", "85", "Yes", "Series", "Well drained", "Fine-loamy, mixed, superactive, thermic Mollic Haploxeralfs",
     "12", "Bt2", "58", "112", "33", "34", "33", "0.5", "7", "0.15", "2.82", None, None],
    ["458994", "170", "Pleasanton loam, 0 to 2 percent slopes, MLRA 14", "CA055", "Napa County, California", "9/16/2026 12:00:00 AM",
     "2", "Cortina", "3", "No", "Series", "Somewhat excessively drained", None,
     None, None, None, None, None, None, None, None, None, None, None, None, None],
]


class Layers(unittest.TestCase):
    def test_texture_triangle(self):
        self.assertEqual(sl.texture_class(40, 40, 20), "loam")
        self.assertEqual(sl.texture_class(33, 34, 33), "clay loam")
        self.assertEqual(sl.texture_class(52, 16, 32), "sandy clay loam")
        self.assertEqual(sl.texture_class(90, 5, 5), "sand")
        self.assertEqual(sl.texture_class(10, 70, 20), "silt loam")
        self.assertEqual(sl.texture_class(20, 20, 60), "clay")
        self.assertIsNone(sl.texture_class(None, 40, 20))

    def test_parse_rows(self):
        mu = sl.parse_layers(ROWS)["458994"]
        self.assertEqual((mu["survey"], mu["survey_version"]), ("Napa County, California (CA055)", "9/16/2026"))
        self.assertEqual([c["name"] for c in mu["components"]], ["Pleasanton", "Cortina"])
        ap, bt = mu["components"][0]["horizons"]
        self.assertEqual((ap["top_cm"], ap["bottom_cm"], ap["texture"], ap["clay_pct"], ap["rock_frag_pct"]), (0, 13, "loam", 20.0, 5))
        # no texture from the survey: computed from sand, silt and clay; no fragments recorded: 0
        self.assertEqual((bt["texture"], bt["rock_frag_pct"]), ("clay loam", 0))
        self.assertEqual(mu["components"][1]["horizons"], [])

    def test_major_and_summary(self):
        mu = sl.parse_layers(ROWS)["458994"]
        comp = sl.major(mu)
        self.assertEqual(comp["name"], "Pleasanton")
        s = sl.summary(comp, 1)
        self.assertEqual(s, [{"top_cm": 0, "bottom_cm": 13, "texture": "loam", "clay_pct": 20.0, "sand_pct": 40.0,
                              "rock_frag_pct": 5.0, "om_pct": 0.75, "pH": 6.5}])

    def test_box(self):
        w = sl.box_wkt(38.5, -122.4, 150)
        self.assertTrue(w.startswith("POLYGON((") and w.count(",") == 4)


if __name__ == "__main__":
    unittest.main()
