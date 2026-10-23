"""Tests for scripts/ssurgo_layers.py (offline)."""
import array
import json
import struct
import sys
import unittest
import zlib
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


ASSETS = Path(__file__).resolve().parent.parent / "prototype" / "assets" / "regions" / "napa_valley"


def png_rgba(path):
    """(width, height, bytes) of an 8-bit RGBA PNG written with filter 0 on every row."""
    d = path.read_bytes()
    w, h = struct.unpack(">II", d[16:24])
    pos, idat = 8, b""
    while pos < len(d):
        n = struct.unpack(">I", d[pos:pos + 4])[0]
        if d[pos + 4:pos + 8] == b"IDAT":
            idat += d[pos + 8:pos + 8 + n]
        pos += 12 + n
    return w, h, zlib.decompress(idat)


class Frame(unittest.TestCase):
    def test_wkt_rings(self):
        rings = sl.wkt_rings("MULTIPOLYGON (((0 0, 1 0, 1 1, 0 0)), ((5 5, 6 5, 6 6, 5 6, 5 5), (5.2 5.2, 5.4 5.2, 5.4 5.4, 5.2 5.2)))")
        self.assertEqual(len(rings), 3)
        self.assertEqual(rings[0][1], (1.0, 0.0))
        # lines and points in a collection are not rings
        self.assertEqual(sl.wkt_rings("GEOMETRYCOLLECTION (POINT (1 2), LINESTRING (0 0, 1 1), POLYGON ((0 0, 2 0, 2 2, 0 0)))"),
                         [[(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 0.0)]])
        self.assertEqual(sl.wkt_rings(None), [])

    def test_fill_keeps_holes_open(self):
        cols = rows = 10
        grid = array.array("H", bytes(2 * cols * rows))
        outer = [(0, 0), (100, 0), (100, 100), (0, 100), (0, 0)]
        hole = [(40, 40), (60, 40), (60, 60), (40, 60), (40, 40)]
        sl.fill_feature(grid, [outer, hole], 7, 0, 100, 10, cols, rows)
        self.assertEqual(grid[0], 7)
        self.assertEqual(grid[5 * cols + 5], 0)        # cell centre (55, 45) is in the hole
        self.assertEqual(sum(1 for v in grid if v == 7), 96)

    def test_slope_and_colours(self):
        self.assertEqual(sl.slope_class("Pleasanton loam, 0 to 2 percent slopes, MLRA 14"), "0 to 2 %")
        self.assertIsNone(sl.slope_class("Water"))
        c = sl.series_colors(["Bressa", "Water", "Goulding", "Rock outcrop"])
        self.assertEqual((c["Water"], c["Rock outcrop"]), (sl.MISC["water"], sl.MISC["rock outcrop"]))
        self.assertNotEqual(c["Bressa"], c["Goulding"])
        self.assertEqual(c, sl.series_colors(["Bressa", "Water", "Goulding", "Rock outcrop"]))

    def test_keep_keys(self):
        mu = sl.parse_layers(ROWS, keep_keys=True)["458994"]
        self.assertEqual(mu["components"][0]["cokey"], "1")
        self.assertEqual(mu["components"][0]["horizons"][0]["chkey"], "11")


class CommittedSoils(unittest.TestCase):
    """soils.json and soils.png as built by --frame for the Napa-Sonoma frame."""

    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads((ASSETS / "soils.json").read_text())
        cls.w, cls.h, cls.raw = png_rgba(ASSETS / "soils.png")

    def test_size_and_grid(self):
        self.assertLess((ASSETS / "soils.json").stat().st_size + (ASSETS / "soils.png").stat().st_size, 4_000_000)
        g = self.meta["grid"]
        self.assertEqual((self.w, self.h), (g["cols"], g["rows"]))
        self.assertEqual({s["areasymbol"] for s in self.meta["surveys"]}, {"CA055", "CA097"})

    def test_indices_and_fields(self):
        n = len(self.meta["units"])
        stride = 4 * self.w + 1
        seen = set()
        for r in range(0, self.h, 7):
            row = self.raw[r * stride + 1:(r + 1) * stride]
            for c in range(0, self.w, 7):
                if row[4 * c + 3]:
                    seen.add(row[4 * c] * 256 + row[4 * c + 1])
        self.assertTrue(seen and min(seen) >= 1 and max(seen) <= n)
        for u in self.meta["units"]:
            self.assertLess(u["series"], len(self.meta["series"]))
            for c in u["components"]:
                self.assertIn("restriction", c)
                for hz in c["horizons"]:
                    self.assertLessEqual(hz["top_cm"], hz["bottom_cm"])
                    self.assertTrue({"texture", "sand_pct", "silt_pct", "clay_pct", "gravel_pct", "om_pct", "pH", "awc"} <= set(hz))

    def test_corison_is_pleasanton(self):
        from fetch_terrain import utm_from_geographic
        e, n = utm_from_geographic(38.484983, -122.44736)
        g = self.meta["grid"]
        c, r = int((e - g["bbox_utm"][0]) // g["cell_m"]), int((g["bbox_utm"][3] - n) // g["cell_m"])
        o = r * (4 * self.w + 1) + 1 + 4 * c
        u = self.meta["units"][self.raw[o] * 256 + self.raw[o + 1] - 1]
        self.assertEqual((u["mukey"], u["slope_class"]), ("458994", "0 to 2 %"))
        self.assertEqual(sl.major({"components": [dict(x, horizons=x["horizons"]) for x in u["components"]]})["name"], "Pleasanton")


if __name__ == "__main__":
    unittest.main()
