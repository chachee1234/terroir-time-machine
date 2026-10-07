"""Checks for the deep-time animation fields (scripts/make_deep_time_fields.py)."""
import json, os, unittest

import numpy as np

P = os.path.join(os.path.dirname(__file__), "..", "prototype/assets/")


class DeepTime(unittest.TestCase):
    def test_mayacamas(self):
        m = json.load(open(P + "regions/napa_valley/mayacamas_8ma.json"))
        g = m["grid"]
        a = np.fromfile(P + "regions/napa_valley/mayacamas_8ma.u8", np.uint8).reshape(2, g["rows"], g["cols"])
        self.assertGreater((a[0] > 128).sum(), 10000)                       # Sonoma Volcanics are mapped here
        te = a[1] * m["scale"]["erupt_ma"]
        self.assertTrue(2.3 <= te.min() and te.max() <= 8.01)
        self.assertGreater(te[-1].mean(), te[0].mean())                       # south (last row) older than north
        self.assertTrue(all(n.startswith("Ts") for n in m["volcanic_units"]))
        names = [f["name"] for f in m["faults"]]
        self.assertIn("Rodgers Creek–Healdsburg Fault", names)
        self.assertIn("Corison", m["places_km"])

    def test_west_coast(self):
        m = json.load(open(P + "plates/west_coast.json"))
        z = np.fromfile(P + "plates/west_coast.i16", "<i2").reshape(m["rows"], m["cols"])
        self.assertLess(z.min(), -3000); self.assertGreater(z.max(), 3000)
        lats = [p[0] for p in m["saf"]]
        self.assertEqual(lats, sorted(lats, reverse=True))                     # north to south
        self.assertGreater(len(m["trench"]), 50)
        for name in ("Pinnacles", "Neenach"):
            self.assertIn(name, m["points"])


if __name__ == "__main__":
    unittest.main()
