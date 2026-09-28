import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_geology_texture as mg  # noqa: E402

TERRAIN = mg.ROOT / "prototype" / "assets" / "terrain.json"


def arc_block(arcs):
    """ARC 2 section: header of seven I10 fields, then two coordinate pairs per line (E14.7)."""
    out = ["ARC  2"]
    for k, (lp, rp, pts) in enumerate(arcs, 1):
        out.append("".join(f"{v:10d}" for v in (k, k, 0, 0, lp, rp, len(pts))))
        vals = [v for p in pts for v in p]
        for j in range(0, len(vals), 4):
            out.append("".join(f"{v:14.7E}" for v in vals[j:j + 4]))
    out.append("".join(f"{v:10d}" for v in (-1, 0, 0, 0, 0, 0, 0)))
    return out


def fdef(name, size, offset, typ, index):
    """INFO item definition line laid out as Arc/INFO writes it (name 16, size 3, offset @21, type @34, index @65)."""
    line = f"{name:<16}{size:3d}{2:2d}{offset:4d}{1:1d}{-1:2d}{size:4d}{-1:2d}{typ:3d}{-1:2d}{-1:4d}{-1:4d}{-1:2d}{'':16}{index:4d}"
    assert line[34:37].strip() == str(typ) and line[65:69].strip() == str(index), line
    return line


def e00_text(arcs, ptypes):
    """A minimal uncompressed E00 with arcs and a PAT (universe polygon first)."""
    rows = ["EXP  0 /TEST/T.E00"] + arc_block(arcs) + ["IFO  2"]
    rows.append(f"{'T.PAT':<32}XX{3:4d}{3:4d}{12 + 35:4d}{len(ptypes) + 1:10d}")
    rows += [fdef("AREA", 4, 1, 60, 1), fdef("T#", 4, 5, 50, 2), fdef("PTYPE", 35, 9, 20, 3)]
    for i, t in enumerate([""] + ptypes, 1):
        rec = f"{0.0:14.7E}{i:11d}{t:<35}"
        rows += [rec[:80], rec[80:]] if len(rec) > 80 else [rec]
    return "\n".join(rows + ["EOI", "EOS"]) + "\n"


def split_square(x0, y0, x1, y1):
    """Square cut at mid-x: polygon 2 = west half (Tswt), 3 = east half (Tslt), 1 = universe outside."""
    xm = (x0 + x1) / 2
    return [(2, 3, [(xm, y0), (xm, y1)]),                     # north along the cut: west = left = 2
            (2, 1, [(xm, y1), (x0, y1), (x0, y0), (xm, y0)]),  # west half boundary, counter-clockwise: inside on the left
            (3, 1, [(xm, y0), (x1, y0), (x1, y1), (xm, y1)])]


class GeologyTextureTest(unittest.TestCase):
    def test_rasterize_assigns_the_polygon_east_of_each_crossing(self):
        arcs = [{"lpoly": lp, "rpoly": rp, "pts": pts} for lp, rp, pts in split_square(0, 0, 1000, 1000)]
        g = mg.rasterize(arcs, -200, 1200, 100, 14, 14)          # grid larger than the square
        self.assertEqual(g[0][0], 0)                            # north-west corner: no crossing to the west
        self.assertEqual([g[7][c] for c in (1, 3, 6, 7, 11, 13)], [0, 2, 2, 3, 3, 1])

    def test_reads_arcs_and_pat(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.e00"
            p.write_text(e00_text(split_square(0, 0, 1000, 1000), ["Tswt", "Tslt"]))
            arcs, pat = mg.read_e00(p)
        self.assertEqual(len(arcs), 3)
        self.assertEqual(arcs[1]["pts"][2], (0.0, 0.0))
        self.assertEqual([r["PTYPE"] for r in pat], ["", "Tswt", "Tslt"])

    def test_datum_offset_is_the_known_northern_california_shift(self):
        de, dn = mg.nad83_to_nad27_offset(531892.63, 4280129.75)
        self.assertTrue(80 < de < 110 and -210 < dn < -180, (de, dn))

    def test_image_size_matches_the_terrain_grid(self):
        meta = json.loads(TERRAIN.read_text())
        x0, y0, x1, y1 = meta["aoi"]["bbox_utm"]
        n = meta["browser_grid"]["cells"]
        with tempfile.TemporaryDirectory() as d:
            e00 = Path(d) / "eswn-geol.e00"          # map in NAD27: cover the block with a margin for the shift
            e00.write_text(e00_text(split_square(x0 - 1000, y0 - 1000, x1 + 1000, y1 + 1000), ["Tswt", "Tslt"]))
            lg = mg.build(e00, TERRAIN, d)
            png = (Path(d) / "geology.png").read_bytes()
        w, h = struct.unpack(">II", png[16:24])
        self.assertEqual((w, h), (n, n))
        self.assertEqual((lg["grid"]["cols"], lg["grid"]["rows"]), (n, n))
        self.assertEqual(lg["unmapped_cells"], 0)
        self.assertEqual({u["ptype"] for u in lg["units"]}, {"Tswt", "Tslt"})
        self.assertEqual(lg["label"], "USGS SIM 2956, 1:100,000")

    def test_committed_drapes_match_their_terrain_grids(self):
        for terrain, png in ((TERRAIN, mg.ROOT / "prototype" / "assets" / "geology.png"),
                             (mg.ROOT / "prototype/assets/regions/napa_valley/terrain.json",
                              mg.ROOT / "prototype/assets/regions/napa_valley/geology.png")):
            if not png.exists():
                continue
            g = json.loads(terrain.read_text())["browser_grid"]
            w, h = struct.unpack(">II", png.read_bytes()[16:24])
            self.assertEqual((w, h), (g.get("cols", g.get("cells")), g.get("rows", g.get("cells"))), png)

    @unittest.skipUnless((mg.ROOT / "data/raw/eswn-geol.e00").exists(), "SIM 2956 E00 not in data/raw (git-ignored)")
    def test_real_map_puts_the_summit_in_tswt(self):
        """STATUS.md M1-05: the GNIS summit falls in polygon 584 (label ID 636), PTYPE Tswt; 4,003 mapped faces."""
        arcs, pat = mg.read_e00(mg.ROOT / "data/raw/eswn-geol.e00")
        self.assertEqual(len(pat) - 1, 4003)
        de, dn = mg.nad83_to_nad27_offset(531892.63, 4280129.75)
        p = mg.rasterize(arcs, 531892.63 + de - 0.5, 4280129.75 + dn + 0.5, 1, 1, 1)[0][0]
        self.assertEqual((p, pat[p - 1]["ESWN_UM-PY7-ID"], pat[p - 1]["PTYPE"]), (584, 636, "Tswt"))

    def test_colours_are_stable_and_distinct(self):
        units = ["Tswt", "Tslt", "KJfs", "Qa", "Tsr", "Tsa", "fsr", "Qls"]
        self.assertEqual(mg.palette(units), mg.palette(list(reversed(units))))
        self.assertEqual(len(set(mg.palette(units).values())), len(units))

    def test_rejects_compressed_e00(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.e00"
            p.write_text("EXP  1 /X/C.E00\n")
            with self.assertRaises(SystemExit):
                mg.read_e00(p)


if __name__ == "__main__":
    unittest.main()
