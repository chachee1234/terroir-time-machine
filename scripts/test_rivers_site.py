"""Tests for make_rivers.py (NHD shapefile reading, channel sizes) and make_site.py (soil horizons, Munsell
colours), plus checks that the committed close-up geology, rivers and Corison site files match their grids."""
import json
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_rivers as mr  # noqa: E402
import make_site as ms  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "prototype" / "assets" / "regions" / "napa_valley"


def dbf(fields, rows):
    """A minimal dBASE III table: fields [(name, type, size)], rows as lists of values."""
    hl = 32 + 32 * len(fields) + 1
    rl = 1 + sum(f[2] for f in fields)
    out = bytearray(struct.pack("<BBBBIHH20x", 3, 126, 1, 1, len(rows), hl, rl))
    for name, typ, size in fields:
        out += name.encode().ljust(11, b"\0") + typ.encode() + b"\0" * 4 + bytes([size, 0]) + b"\0" * 14
    out += b"\r"
    for r in rows:
        out += b" " + b"".join((str(v).rjust(f[2]) if f[1] == "N" else str(v).ljust(f[2])).encode() for v, f in zip(r, fields))
    return bytes(out + b"\x1a")


def shp_polylines(lines):
    """A PolyLine (type 3) shapefile body with one part per record."""
    recs = b""
    for k, pts in enumerate(lines, 1):
        body = struct.pack("<i4d2i", 3, 0, 0, 0, 0, 1, len(pts)) + struct.pack("<i", 0) + b"".join(struct.pack("<2d", *p) for p in pts)
        recs += struct.pack(">ii", k, len(body) // 2) + body
    head = struct.pack(">i20xi", 9994, (100 + len(recs)) // 2) + struct.pack("<ii4d4d", 1000, 3, 0, 0, 0, 0, 0, 0, 0, 0)
    return head + recs


class RiversTest(unittest.TestCase):
    def test_reads_dbf_and_polylines(self):
        rows = mr.read_dbf(dbf([("gnis_name", "C", 12), ("ftype", "N", 4)], [["Napa River", 460], ["", 558]]))
        self.assertEqual(rows, [{"gnis_name": "Napa River", "ftype": 460}, {"gnis_name": "", "ftype": 558}])
        geoms = mr.read_polylines(shp_polylines([[(-122.4, 38.5), (-122.39, 38.49)], [(0, 0), (1, 1), (2, 1)]]))
        self.assertEqual(geoms[1], [[(0, 0), (1, 1), (2, 1)]])

    def test_upstream_length_adds_tributaries_and_splits_braids(self):
        # a -> c, b -> c (tributaries); c splits into d and e, which rejoin in f
        L = {"a": [(0, 2), (1, 1)], "b": [(2, 2), (1, 1)], "c": [(1, 1), (1, 0)], "d": [(1, 0), (0.5, -1)],
             "e": [(1, 0), (1.5, -1)], "f": [(0.5, -1), (1, -2)], "g": [(1.5, -1), (0.5, -1)]}
        keys = list(L)
        acc = dict(zip(keys, mr.upstream_km([L[k] for k in keys], [1.0] * len(keys))))
        self.assertEqual(acc["c"], 3.0)
        self.assertEqual(acc["d"], 2.5)                      # half of c's 3 km plus itself
        self.assertAlmostEqual(acc["f"], 1 + 2.5 + (2.5 + 1))  # via d and via e+g: c's 3 km arrives once, half down each branch
        self.assertEqual([mr.size_class(k) for k in (3, 10, 39, 40, 999, 1000)], [1, 2, 2, 3, 5, 6])

    def test_simplify_and_clip(self):
        line = [(0, 0), (5, 0.4), (10, 0), (15, 8), (20, 0)]
        self.assertEqual(mr.simplify(line, 1.0), [(0, 0), (10, 0), (15, 8), (20, 0)])
        self.assertEqual(mr.clip_runs([(0, 0), (5, 5), (50, 50), (6, 6), (7, 7)], (0, 0, 10, 10)), [[(0, 0), (5, 5)], [(6, 6), (7, 7)]])

    def test_committed_rivers(self):
        d = json.loads((ASSETS / "rivers.json").read_text())
        x0, y0, x1, y1 = d["bbox_utm"]
        self.assertIn("Napa River", d["names"])
        for r in d["lines"][:500]:
            self.assertTrue(1 <= r[1] <= 6 and x0 - 1 <= r[3] <= x1 + 1 and y0 - 1 <= r[4] <= y1 + 1)
        napa = max(r[1] for r in d["lines"] if r[0] == d["names"].index("Napa River"))
        self.assertEqual(napa, 6)


class SiteTest(unittest.TestCase):
    def test_munsell_colours_order_by_value(self):
        dark, light = ms.munsell_rgb("10YR", 2, 1), ms.munsell_rgb("10YR", 6, 3)
        lum = lambda h: sum(int(h[i:i + 2], 16) for i in (1, 3, 5))
        self.assertLess(lum(dark), lum(light))
        self.assertIsNone(ms.munsell_rgb("10YR", None, 2))

    def test_merge_colours_prefers_same_master_horizon(self):
        osd = [{"name": "A1", "top_cm": 23, "bottom_cm": 53, "rgb": "#a"}, {"name": "B2t", "top_cm": 53, "bottom_cm": 122, "rgb": "#b"}]
        hz = ms.merge_colours([{"name": "Bt1", "top_cm": 45, "bottom_cm": 58, "rock_frag_pct": 0}], osd)
        self.assertEqual((hz[0]["osd_horizon"], hz[0]["rgb"], hz[0]["gravel_pct"]), ("B2t", "#b", None))

    def test_horizons_keep_texture_modifier_and_gravel(self):
        doc = {"HORIZONS": [[{"name": "IIC1", "top": 112, "bottom": 127, "texture_class": "sandy loam",
                              "moist_hue": "10YR", "moist_value": 3, "moist_chroma": 3, "pH": 6.3,
                              "narrative": "IIC1--44 to 50 inches; pale brown (10YR 6/3) gravelly sandy loam, dark brown (10YR 3/3) moist; about 20 percent fine gravel"}]]}
        h = ms.horizons(doc)[0]
        self.assertEqual((h["texture"], h["gravel_pct"], h["buried"]), ("gravelly sandy loam", 20, False))

    def test_committed_corison_site(self):
        s = json.loads((ASSETS / "sites" / "corison.json").read_text())
        self.assertEqual(s["geology"]["at_site"], "Qf")
        self.assertIn("st__helena", [a["id"] for a in s["avas"]])
        hz = s["soil"]["horizons"]
        self.assertTrue(all(a["bottom_cm"] == b["top_cm"] for a, b in zip(hz, hz[1:])))
        # the USDA soil survey maps Pleasanton loam at the winery; Bale is only reported (unverified)
        so = s["soil"]
        self.assertEqual((so["series"], so["mapped"]["component"]), ("PLEASANTON", "Pleasanton"))
        self.assertEqual(so["reported"]["status"], "unverified")
        self.assertEqual([h["name"] for h in hz][:2], ["Ap", "A"])
        for h in hz:
            self.assertAlmostEqual(h["sand_pct"] + h["silt_pct"] + h["clay_pct"], 100, delta=1)
            self.assertTrue(h["rgb"], h["name"])
        self.assertEqual([h["osd_horizon"][0] for h in hz], [h["name"][0] for h in hz])  # colours from the same master horizon
        self.assertIn(so["reported"]["source"], s["sources"])
        sec = s["section"]
        self.assertEqual(len(sec["ground_m"]), int(round(2 * sec["half_m"] / sec["step_m"])) + 1)
        self.assertIn("Napa River", [c["name"] for c in sec["streams"]])
        for k in [c["source"] for c in s["claims"]] + [s["location"]["source"], s["soil"]["source"]]:
            self.assertIn(k, s["sources"])


class CloseupGeologyTest(unittest.TestCase):
    def test_pngs_match_their_closeup_grids(self):
        idx = {q["id"]: q for q in json.loads((ASSETS / "detail" / "index.json").read_text())["locations"]}
        doc = json.loads((ASSETS / "detail" / "geology.json").read_text())
        self.assertIn("corison", [c["id"] for c in doc["closeups"]])
        for c in doc["closeups"]:
            png = (ASSETS / "detail" / c["file"]).read_bytes()
            w, h = struct.unpack(">II", png[16:24])
            self.assertEqual((w, h), (idx[c["id"]]["cols"], idx[c["id"]]["rows"]), c["id"])


if __name__ == "__main__":
    unittest.main()
