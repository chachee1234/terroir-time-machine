"""Tests for make_plate_model.py (quaternion maths) and the committed muller2019.json: unit quaternions, today
unrotated, polygon encoding, and the Atlantic closing up when South America and Africa are rotated back."""
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_plate_model as pm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSET = ROOT / "prototype" / "assets" / "plates" / "muller2019.json"


def unit(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))


def km(a, b):
    return 6371 * math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b)))))


class QuaternionMaths(unittest.TestCase):
    def test_pole_rotation(self):
        # 90 degrees about the north pole carries (0 N, 0 E) to (0 N, 90 E)
        v = pm.q_rotate(pm.q_pole(90, 0, 90), unit(0, 0))
        self.assertLess(km(v, unit(0, 90)), 1e-3)

    def test_slerp_ends_and_middle(self):
        a, b = pm.q_pole(90, 0, 0), pm.q_pole(90, 0, 60)
        for t, want in ((0, 0), (1, 60), (0.5, 30)):
            v = pm.q_rotate(pm.q_slerp(a, b, t), unit(0, 0))
            self.assertLess(km(v, unit(0, want)), 1e-3)

    def test_composition(self):
        q = pm.q_mul(pm.q_pole(90, 0, 30), pm.q_pole(90, 0, 15))
        self.assertLess(km(pm.q_rotate(q, unit(10, 0)), unit(10, 45)), 1e-3)


class CommittedAsset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads(ASSET.read_text())
        cls.n = len(cls.d["ages"])

    def quat(self, plate, age):
        i, k = self.d["plates"].index(plate), self.d["ages"].index(age)
        o = (i * self.n + k) * 4
        return tuple(self.d["quats"][o:o + 4])

    def test_shape_and_rights(self):
        d = self.d
        self.assertEqual(len(d["quats"]), len(d["plates"]) * self.n * 4)
        self.assertEqual(d["ages"][0], 0)
        self.assertIn("CC BY 3.0", d["rights"])
        for p in d["polys"]:
            self.assertEqual((len(p) - 3) % 2, 0)
            self.assertLess(p[0], len(d["plates"]))
            self.assertGreaterEqual(p[1], p[2])

    def test_unit_and_today_unrotated(self):
        q = self.d["quats"]
        for o in range(0, len(q), 4):
            self.assertAlmostEqual(math.sqrt(sum(x * x for x in q[o:o + 4])), 1.0, delta=2e-3)
        for p in self.d["plates"]:
            self.assertAlmostEqual(abs(self.quat(p, 0)[0]), 1.0, delta=1e-3)

    def test_atlantic_closes(self):
        # Recife (Brazil) and Douala (Cameroon) are ~4,900 km apart today and sat next to each other in Pangaea
        recife, douala = unit(-8.05, -34.88), unit(4.05, 9.70)
        self.assertGreater(km(recife, douala), 4500)
        a = pm.q_rotate(self.quat(201, 200), recife)
        b = pm.q_rotate(self.quat(701, 200), douala)
        self.assertLess(km(a, b), 300)

    def test_napa_moves_with_north_america(self):
        # the site is on plate 101 today and sits a few degrees east at 30 Ma, in the mantle frame
        site = unit(38.6694, -122.6333)
        then = pm.q_rotate(self.quat(101, 30), site)
        self.assertGreater(km(site, then), 200)
        self.assertLess(km(site, then), 2000)


if __name__ == "__main__":
    unittest.main()
