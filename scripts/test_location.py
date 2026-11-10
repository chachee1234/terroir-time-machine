"""Tier 0 tests for locations outside California (build_location.py and prototype/gibraltar.html). No network."""
import hashlib
import json
import re
import sys
import unittest
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_location as bl  # noqa: E402

ROOT = bl.ROOT
LOC = ROOT / "data" / "locations" / "gibraltar.json"


class LocationTest(unittest.TestCase):
    def test_frame_shape_gives_square_cells(self):
        cols, rows = bl.frame_shape([-6.6, 35.35, -4.4, 36.55], 720)
        self.assertEqual(cols, 720)
        self.assertAlmostEqual(rows, 720 * 1.2 / (2.2 * 0.8087), delta=2)

    def test_tiles_cover_the_frame(self):
        tiles = bl.tiles_for_lonlat([-6.6, 35.35, -4.4, 36.55], 10)
        for lat, lon in [(35.35, -6.6), (36.55, -4.4), (36.0, -5.6)]:
            x, y = bl.merc_px(lat, lon, 10)
            self.assertIn((int(x) // 256, int(y) // 256), tiles)

    def test_committed_grids_match_their_metadata(self):
        loc = json.loads(LOC.read_text())
        meta = json.loads((ROOT / loc["assets_dir"] / "terrain.json").read_text())
        self.assertEqual([f["id"] for f in meta["frames"]], [f["id"] for f in loc["frames"]])
        for f in meta["frames"]:
            path = ROOT / loc["assets_dir"] / f["file"]
            raw = path.read_bytes()
            self.assertEqual(len(raw), f["cols"] * f["rows"] * 2, f["id"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), f["sha256"], f["id"])
            g = array("h")
            g.frombytes(raw)
            if sys.byteorder != "little":
                g.byteswap()
            self.assertEqual((min(g), max(g)), (f["min_m"], f["max_m"]))

    def test_strait_grid_has_the_sill_and_the_deep_alboran(self):
        loc = json.loads(LOC.read_text())
        meta = json.loads((ROOT / loc["assets_dir"] / "terrain.json").read_text())
        f = next(x for x in meta["frames"] if x["id"] == "strait")
        g = array("h")
        g.frombytes((ROOT / loc["assets_dir"] / f["file"]).read_bytes())
        lon0, lat0, lon1, lat1 = f["bbox_lonlat"]
        W, R = f["cols"], f["rows"]

        def col_min(lon):
            c = int((lon - lon0) / (lon1 - lon0) * W)
            rows = [int((lat1 - la / 100) / (lat1 - lat0) * R) for la in range(3580, 3610)]
            return min(g[r * W + c] for r in rows)
        # Camarinal Sill is 284 m deep (Garcia-Castellanos et al. 2009); the resampled grid's shallowest
        # channel crossing near it must be within about 100 m of that, and the strait deepens eastwards.
        sill = max(col_min(lon / 100) for lon in range(-580, -569))
        self.assertLess(abs(sill + 284), 100, sill)
        self.assertLess(col_min(-4.6), -1000)

    def test_viewer_chapters_run_oldest_to_youngest_and_are_labelled(self):
        page = (ROOT / "prototype" / "gibraltar.html").read_text(encoding="utf-8")
        ages = [tuple(float(x) for x in m) for m in re.findall(r'age:\[([\d.]+),([\d.]+)\]', page)]
        self.assertGreaterEqual(len(ages), 6)
        for (a0, a1), (b0, _) in zip(ages, ages[1:]):
            self.assertGreaterEqual(a0, a1)
            self.assertGreaterEqual(a1, b0 - 1e-9)
        chapters = re.findall(r'\{id:"(\w+)"[^\n]*\n[^\n]*\n\s*cls:(\w+)', page)
        self.assertTrue(chapters)
        self.assertIn("Illustrative process · geometry and timing are schematic", page)
        for cid, cls in chapters:
            self.assertEqual(cls, "MEAS" if cid == "today" else "ILLUS", cid)
        self.assertIn('href="timemachine.html"', page)
        napa = (ROOT / "prototype" / "timemachine.html").read_text(encoding="utf-8")
        self.assertIn('href="gibraltar.html"', napa)


if __name__ == "__main__":
    unittest.main()
