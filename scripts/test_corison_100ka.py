"""Checks for the Corison 100,000-year fields (scripts/make_corison_100ka.py)."""
import json, os, unittest

import numpy as np

A = os.path.join(os.path.dirname(__file__), "..", "prototype/assets/regions/napa_valley/sites/")


class Corison100ka(unittest.TestCase):
    def setUp(self):
        self.m = json.load(open(A + "corison_100ka.json"))
        g = self.m["grid"]
        self.f = np.fromfile(A + "corison_100ka.u8", np.uint8).reshape(len(self.m["fields"]), g["rows"], g["cols"])

    def test_shape_and_fields(self):
        self.assertEqual(self.m["fields"], ["pleist", "fan", "hol", "incise", "creeks", "vines", "young"])
        self.assertEqual(self.f.shape[1:], (501, 501))

    def test_thickness_limits(self):
        F = dict(zip(self.m["fields"], self.f))
        t = self.m["thickness_m"]
        self.assertLessEqual(F["pleist"].max() * self.m["scale"]["pleist"], t["pleistocene_fill"] + 1e-6)
        self.assertLessEqual(F["hol"].max() * self.m["scale"]["hol"], t["holocene"] + 1e-6)
        self.assertIn("not measured", t["status"])

    def test_no_fill_on_the_hills(self):
        F = dict(zip(self.m["fields"], self.f))
        hills = F["young"] == 0
        self.assertTrue(hills.any())
        for k in ("pleist", "fan", "hol"):
            self.assertEqual(int(F[k][hills].max()), 0, k)

    def test_site_and_fault_in_frame(self):
        x, y = self.m["site_local_m"]
        self.assertAlmostEqual(x, 2500, delta=1); self.assertAlmostEqual(y, 2500, delta=1)
        self.assertEqual(self.m["fault"]["name"], "West Napa Fault")


if __name__ == "__main__":
    unittest.main()
