"""Tests for make_historical_ecology.py (file-geodatabase varints, State Plane inverse) and checks that the
committed historical_ecology.json lines up with today's Napa River and with the Corison site file."""
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_historical_ecology as mh  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "prototype" / "assets" / "regions" / "napa_valley"
WKT = ('PROJCS["NAD_1983_StatePlane_California_II_FIPS_0402_Feet",GEOGCS["GCS_North_American_1983",'
       'DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],'
       'UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],'
       'PARAMETER["False_Easting",6561666.666666666],PARAMETER["False_Northing",1640416.666666667],'
       'PARAMETER["Central_Meridian",-122.0],PARAMETER["Standard_Parallel_1",38.33333333333334],'
       'PARAMETER["Standard_Parallel_2",39.83333333333334],PARAMETER["Latitude_Of_Origin",37.66666666666666],'
       'UNIT["Foot_US",0.3048006096012192]]')


class Reader(unittest.TestCase):
    def test_varints(self):
        self.assertEqual(mh.varuint(bytes([0x96, 0x01]), 0), (150, 2))
        self.assertEqual(mh.varint(bytes([0x45]), 0), (-5, 1))
        self.assertEqual(mh.varint(bytes([0x81, 0x01]), 0), (65, 2))

    def test_state_plane_origin(self):
        lat, lon = mh.lcc_inverse(WKT)(6561666.666666666, 1640416.666666667)   # false origin
        self.assertAlmostEqual(lat, 37.666666667, places=6)
        self.assertAlmostEqual(lon, -122.0, places=6)


class Committed(unittest.TestCase):
    def test_mainstem_on_napa_river(self):
        he = json.loads((ASSETS / "historical_ecology.json").read_text())
        rv = json.loads((ASSETS / "rivers.json").read_text())
        napa = [mh.decode(r, 3) for r in rv["lines"] if r[0] >= 0 and rv["names"][r[0]] == "Napa River"]
        ms = he["classes"]["channels"].index("Mainstem Channel")
        pts = [p for r in he["channels"] if r[0] == ms for p in mh.decode(r, 3)[::25]][:60]

        def dist(p, line):
            best = math.inf
            for (ax, ay), (bx, by) in zip(line, line[1:]):
                dx, dy = bx - ax, by - ay
                t = max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / ((dx * dx + dy * dy) or 1)))
                best = min(best, math.hypot(ax + t * dx - p[0], ay + t * dy - p[1]))
            return best
        d = sorted(min(dist(p, l) for l in napa) for p in pts)
        self.assertLess(d[len(d) // 2], 60)          # same river, two centuries apart: tens of metres

    def test_site_block(self):
        site = json.loads((ASSETS / "sites" / "corison.json").read_text())
        h = site["historical"]
        self.assertIn(h["source"], site["sources"])
        self.assertEqual(h["habitat_at_site"]["type"], "Valley Oak Savanna")


if __name__ == "__main__":
    unittest.main()
