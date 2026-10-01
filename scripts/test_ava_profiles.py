"""Tests for scripts/make_ava_profiles.py and its committed output (offline)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_ava_profiles as m  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "prototype/assets/regions/napa_valley/ava_profiles.json"


class Helpers(unittest.TestCase):
    def test_ring_mask_square(self):
        # 1 km square, 100 m cells centred on 50 m: 10 x 10 cells inside
        ring = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        mask = m.ring_mask([ring], 50, 1950, 100, 20, 20)
        self.assertEqual(sum(mask), 100)

    def test_area(self):
        self.assertAlmostEqual(m.polygon_area_km2([[(0, 0), (2, 0), (2, 3), (0, 3)]]), 6.0)

    def test_soil_name(self):
        self.assertEqual(m.soil_name("Bale clay loam, 0 to 2 percent slopes"), "Bale clay loam")
        self.assertEqual(m.soil_name("Hambright-Rock outcrop complex, 30 to 75 percent slopes"), "Hambright-Rock outcrop complex")

    def test_unit_names(self):
        met = ROOT / "data/raw/sim2956d.met.txt"
        if not met.exists():
            self.skipTest("SIM 2956 metadata not downloaded (data/raw is not committed)")
        self.assertEqual(m.unit_names(met).get("Qhf"), "Alluvial fan deposits (Holocene)")


class Output(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(OUT.read_text())

    def test_every_closeup_ava_has_a_profile(self):
        idx = json.loads((OUT.parent / "detail/index.json").read_text())["locations"]
        ids = {q["id"] for q in idx if q.get("kind", "ava") == "ava"}
        self.assertTrue(ids)
        self.assertEqual(ids - set(self.d["avas"]), set())

    def test_profile_values_are_sane(self):
        for aid, a in self.d["avas"].items():
            e = a["elevation_m"]
            self.assertLessEqual(e["min"], e["p10"], aid)
            self.assertLessEqual(e["p10"], e["median"], aid)
            self.assertLessEqual(e["median"], e["p90"], aid)
            self.assertLessEqual(e["p90"], e["max"], aid)
            self.assertLess(e["max"], 1400, aid)            # nothing in the frame tops Mount St. Helena
            self.assertGreater(a["area_km2"], 1, aid)
            self.assertLessEqual(sum(u["pct"] for u in a.get("geology", [])), 100.1, aid)
            if a.get("soils"):
                self.assertLessEqual(sum(u["pct"] for u in a["soils"]["map_units"]), 100.1, aid)

    def test_producers_carry_sources(self):
        for aid, a in self.d["avas"].items():
            pr = a.get("producers")
            if pr:
                self.assertTrue(pr["producers"], aid)
                self.assertTrue(all(u.startswith("https://") for u in pr["sources"]), aid)
        self.assertIn("unverified", self.d["sources"]["producers"])

    def test_rutherford_matches_the_maps(self):
        r = self.d["avas"]["rutherford"]
        self.assertEqual(r["geology"][0]["ptype"], "Qhf")   # valley-floor fans, SIM 2956
        self.assertLess(r["elevation_m"]["median"], 100)


if __name__ == "__main__":
    unittest.main()
