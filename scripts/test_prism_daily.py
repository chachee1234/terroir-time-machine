"""Tests for fetch_prism_daily.py (texel-to-cell map, year packing) and a check that the committed daily files
match their index.json."""
import datetime
import json
import sys
import tempfile
import unittest
from array import array
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_prism_daily as fp  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REGION = json.loads((ROOT / "data" / "regions" / "napa_valley.json").read_text())
DAILY = ROOT / REGION["assets_dir"] / "daily"
GRID = {"lon0": -122.979167, "lat0": 38.854167, "dlon": 1 / 24, "dlat": 1 / 24, "cols": 24, "rows": 20}


class TextureMap(unittest.TestCase):
    def test_every_texel_lands_in_the_grid(self):
        t = fp.texture_map(REGION, GRID)
        self.assertEqual((t["cols"], t["rows"]), (76, 76))
        self.assertEqual(len(t["cell"]), 76 * 76)
        self.assertTrue(all(0 <= c < 24 * 20 for c in t["cell"]))

    def test_north_row_first(self):
        t = fp.texture_map(REGION, GRID)
        first_rows = {c // 24 for c in t["cell"][:76]}
        last_rows = {c // 24 for c in t["cell"][-76:]}
        self.assertLess(max(first_rows), min(last_rows))


class Pack(unittest.TestCase):
    def test_round_trip(self):
        region = dict(REGION, id="test_region")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            cache = tmp / "cache"
            (cache).mkdir()
            (cache / "grid.json").write_text(json.dumps({"window": [0, 0, 2, 2], "grid": dict(GRID, cols=2, rows=2)}))
            day = datetime.date(1984, 3, 2)
            for var, vals in (("tmax", [21.04, 22.0, float("nan"), 19.5]), ("tmin", [3.0, 4.0, 5.0, 6.0]),
                              ("ppt", [0.0, 12.3, 0.0, 0.0])):
                (cache / var).mkdir()
                (cache / var / f"{day:%Y%m%d}.f32").write_bytes(array("f", vals).tobytes())
            with mock.patch.object(fp, "cache_dir", return_value=cache), mock.patch.object(fp, "ROOT", tmp):
                index, out = fp.pack(dict(region, assets_dir="assets"))
            self.assertEqual(index["years"], [{"year": 1984, "days": 366, "days_with_data": 1}])
            self.assertEqual(index["last_day"], "1984-03-02")
            a = array("h")
            a.frombytes((out / "1984.bin").read_bytes())
            self.assertEqual(len(a), 3 * 366 * 4)
            doy = (day - datetime.date(1984, 1, 1)).days
            self.assertEqual(list(a[doy * 4: doy * 4 + 4]), [210, 220, fp.NODATA, 195])
            self.assertEqual(a[(2 * 366 + doy) * 4 + 1], 123)
            self.assertEqual(a[0], fp.NODATA)


class Committed(unittest.TestCase):
    def test_files_match_index(self):
        if not (DAILY / "index.json").exists():
            self.skipTest("no daily weather built")
        m = json.loads((DAILY / "index.json").read_text())
        ncell = m["grid"]["cols"] * m["grid"]["rows"]
        self.assertEqual(len(m["texture"]["cell"]), m["texture"]["cols"] * m["texture"]["rows"])
        for y in m["years"]:
            self.assertEqual((DAILY / f"{y['year']}.bin").stat().st_size, 2 * len(m["vars"]) * y["days"] * ncell)


if __name__ == "__main__":
    unittest.main()
