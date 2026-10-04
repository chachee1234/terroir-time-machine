"""Tests for make_dwr_vineyards.py: projections from the .prj, the streamed shapefile/dBASE reader, crop
classification and the scanline fill, on a small synthetic DWR-style ZIP (no network)."""
import io
import json
import math
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_dwr_vineyards as dv  # noqa: E402
import make_vineyards as mv  # noqa: E402
from fetch_tiles import geographic_from_utm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REGION = ROOT / "data" / "regions" / "napa_valley.json"
WEBMERC_PRJ = ('PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",'
               'SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],'
               'PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],'
               'PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],'
               'PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]]')
TEALE_PRJ = ('PROJCS["NAD_1983_California_Teale_Albers",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",'
             'SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],'
             'PROJECTION["Albers"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",-4000000.0],'
             'PARAMETER["Central_Meridian",-120.0],PARAMETER["Standard_Parallel_1",34.0],'
             'PARAMETER["Standard_Parallel_2",40.5],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]')


def write_zip(path, prj, rows, fields=(("MAIN_CROP", 6), ("ACRES", 12))):
    """rows: [(rings in prj coordinates, {field: value})]. Writes .shp/.shx/.dbf/.prj into a ZIP subfolder."""
    shp, shx = io.BytesIO(), io.BytesIO()
    allx = [x for rings, _ in rows for ring in rings for x, _y in ring]
    ally = [y for rings, _ in rows for ring in rings for _x, y in ring]
    off = 50
    for i, (rings, _) in enumerate(rows):
        pts = [p for ring in rings for p in ring]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        body = struct.pack("<i4d2i", 5, min(xs), min(ys), max(xs), max(ys), len(rings), len(pts))
        k = 0
        for ring in rings:
            body += struct.pack("<i", k)
            k += len(ring)
        body += b"".join(struct.pack("<2d", *p) for p in pts)
        shp.write(struct.pack(">2i", i + 1, len(body) // 2) + body)
        shx.write(struct.pack(">2i", off, len(body) // 2))
        off += 4 + len(body) // 2
    head = lambda n: (struct.pack(">7i", 9994, 0, 0, 0, 0, 0, n) + struct.pack("<2i4d4d", 1000, 5, min(allx), min(ally),
                                                                                max(allx), max(ally), 0, 0, 0, 0))
    shp_b = head(50 + len(shp.getvalue()) // 2) + shp.getvalue()
    shx_b = head(50 + len(shx.getvalue()) // 2) + shx.getvalue()
    rlen = 1 + sum(w for _, w in fields)
    dbf = bytearray(struct.pack("<B3BIHH20x", 3, 126, 1, 1, len(rows), 32 + 32 * len(fields) + 1, rlen))
    for name, w in fields:
        dbf += name.encode().ljust(11, b"\0") + b"C" + b"\0" * 4 + bytes([w, 0]) + b"\0" * 14
    dbf += b"\x0d"
    for _, attrs in rows:
        dbf += b" " + b"".join(str(attrs.get(n, "")).encode().ljust(w)[:w] for n, w in fields)
    dbf += b"\x1a"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for ext, data in ((".shp", shp_b), (".shx", shx_b), (".dbf", bytes(dbf)), (".prj", prj.encode())):
            z.writestr("i15_Crop_Mapping_test/i15_Crop_Mapping_test" + ext, data)


def square(e, n, side, proj):
    """A closed clockwise ring (shapefile outer ring order) of a UTM square, in the shapefile's coordinates."""
    c = [(e, n), (e, n + side), (e + side, n + side), (e + side, n), (e, n)]
    return [proj.forward(*geographic_from_utm(x, y)) for x, y in c]


class Projections(unittest.TestCase):
    def test_albers_matches_cdl_forward(self):
        al = dv.Albers(29.5, 45.5, 23.0, -96.0)                              # EPSG:5070, as in make_vineyards
        for lat, lon in ((38.48, -122.45), (23.0, -96.0), (45.0, -70.0)):
            for got, want in zip(al.forward(lat, lon), mv.albers(lat, lon)):
                self.assertAlmostEqual(got, want, places=4)

    def test_round_trips(self):
        for prj in (WEBMERC_PRJ, TEALE_PRJ):
            _name, p = dv.crs_from_prj(prj)
            for lat, lon in ((38.484983, -122.44736), (32.7, -117.1), (41.9, -124.1)):
                la, lo = p.inverse(*p.forward(lat, lon))
                self.assertAlmostEqual(la, lat, places=9)
                self.assertAlmostEqual(lo, lon, places=9)

    def test_teale_origin(self):
        _n, p = dv.crs_from_prj(TEALE_PRJ)
        x, y = p.forward(0.0, -120.0)
        self.assertAlmostEqual(x, 0, places=3)
        self.assertAlmostEqual(y, -4000000, places=3)

    def test_unsupported(self):
        with self.assertRaises(SystemExit):
            dv.crs_from_prj('PROJCS["x",PROJECTION["Lambert_Conformal_Conic"],UNIT["Meter",1.0]]')


class Fill(unittest.TestCase):
    def test_square_and_hole(self):
        outer = [(0, 0), (0, 200), (200, 200), (200, 0)]
        hole = [(60, 60), (140, 60), (140, 140), (60, 140)]
        n = lambda sp: sum(c1 - c0 + 1 for ss in sp.values() for c0, c1 in ss)
        self.assertEqual(n(dv.spans([outer], 0, 200, 20, 10, 10)), 100)
        self.assertEqual(n(dv.spans([outer, hole], 0, 200, 20, 10, 10)), 100 - 16)

    def test_clipped_to_grid(self):
        big = [(-500, -500), (-500, 500), (500, 500), (500, -500)]
        sp = dv.spans([big], 0, 100, 20, 5, 5)
        self.assertEqual(sorted(sp), list(range(5)))
        self.assertTrue(all(ss == [(0, 4)] for ss in sp.values()))


class Build(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def make(self, prj, field="MAIN_CROP", vine="V", other="D12"):
        _n, p = dv.crs_from_prj(prj)
        rows = [([square(548000, 4259600, 200, p)], {field: vine, "ACRES": "9.88"}),       # Corison, St. Helena AVA
                ([square(548400, 4259600, 200, p)], {field: other, "ACRES": "9.88"}),      # an orchard next door
                ([square(400000, 3800000, 200, p)], {field: vine, "ACRES": "9.88"})]       # far outside the frame
        z = self.dir / "dwr.zip"
        write_zip(z, prj, rows, ((field, 24), ("ACRES", 12)))
        return z

    def test_web_mercator_zip(self):
        out = dv.build(REGION, [2023], self.make(WEBMERC_PRJ), out_dir=self.dir, update_index=False)
        y = out["years"]["2023"]
        self.assertEqual(y["field"], "MAIN_CROP")
        self.assertEqual(y["matched_values"], {"V": 1})
        self.assertEqual(y["fields_in_frame"], 1)
        self.assertEqual(y["dwr_acres_in_frame"], 10)
        self.assertTrue(9 <= y["frame_acres"] <= 11, y["frame_acres"])
        self.assertTrue(9 <= y["ava_acres"]["St. Helena"] <= 11)
        self.assertTrue(9 <= y["ava_acres"]["Napa Valley"] <= 11)
        self.assertEqual(y["ava_acres"]["Los Carneros"], 0)
        png = (self.dir / "vineyard_fields.png").read_bytes()
        self.assertEqual(list(struct.unpack(">II", png[16:24])), out["frame_cells"])
        self.assertEqual(out["frame_cells"], [3810, 3825])
        self.assertEqual(json.loads((self.dir / "vineyard_fields.json").read_text())["drape"]["year"], 2023)

    def test_teale_and_name_field(self):
        z = self.make(TEALE_PRJ, field="DWR_STANDA", vine="V | VINEYARD", other="D | DECIDUOUS FRUITS AND NUTS")
        y = dv.build(REGION, [2016], z, out_dir=self.dir, update_index=False)["years"]["2016"]
        self.assertEqual(y["field"], "DWR_STANDA")
        self.assertTrue(9 <= y["frame_acres"] <= 11)

    def test_no_vines_says_what_it_saw(self):
        z = self.make(WEBMERC_PRJ, vine="T19", other="D12")
        with self.assertRaises(SystemExit) as cm:
            dv.build(REGION, [2023], z, out_dir=self.dir, update_index=False)
        self.assertIn("D12", str(cm.exception))

    def test_unknown_field_lists_fields(self):
        z = self.make(WEBMERC_PRJ, field="CROPNAME")
        with self.assertRaises(SystemExit) as cm:
            dv.build(REGION, [2023], z, out_dir=self.dir, update_index=False)
        self.assertIn("CROPNAME", str(cm.exception))


class Committed(unittest.TestCase):
    """Once the real drape is built, it must match its grid and be listed for the viewer."""
    ASSETS = ROOT / "prototype" / "assets" / "regions" / "napa_valley"

    def test_committed_drape(self):
        p = self.ASSETS / "vineyard_fields.json"
        if not p.exists():
            self.skipTest("vineyard_fields.json not built yet (run make_dwr_vineyards.py)")
        v = json.loads(p.read_text())
        png = (self.ASSETS / "vineyard_fields.png").read_bytes()
        self.assertEqual(list(struct.unpack(">II", png[16:24])), v["frame_cells"])
        latest = v["years"][str(v["drape"]["year"])]
        self.assertGreater(latest["ava_acres"]["Napa Valley"], latest["ava_acres"]["St. Helena"])
        idx = json.loads((ROOT / "prototype" / "assets" / "regions" / "index.json").read_text())
        self.assertIn("vineyard_fields", next(r for r in idx["regions"] if r["id"] == "napa_valley")["layers"])


if __name__ == "__main__":
    unittest.main()
