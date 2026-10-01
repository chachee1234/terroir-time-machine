"""Tests for make_climate.py (TIFF LZW, Winkler classes, cell lookup) and make_vineyards.py (Albers projection,
AVA scanline fill), plus checks that the committed climate.json and vineyards.json match their grids."""
import json
import struct
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_climate as mc  # noqa: E402
import make_vineyards as mv  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "prototype" / "assets" / "regions" / "napa_valley"


def lzw_encode(data):
    """Reference TIFF LZW encoder (MSB-first, early change) for the decoder test."""
    table = {bytes([i]): i for i in range(256)}
    codes, bits, w = [256], 9, b""
    widths = [9]
    for ch in data:
        wc = w + bytes([ch])
        if wc in table:
            w = wc
            continue
        codes.append(table[w])
        widths.append(bits)
        table[wc] = len(table) + 2
        if len(table) + 2 >= (1 << bits) and bits < 12:   # libtiff: switch when the next free code needs it
            bits += 1
        w = bytes([ch])
    codes += [table[w], 257]
    widths += [bits, bits]
    acc, n, out = 0, 0, bytearray()
    for c, b in zip(codes, widths):
        acc, n = (acc << b) | c, n + b
        while n >= 8:
            n -= 8
            out.append((acc >> n) & 0xFF)
    if n:
        out.append((acc << (8 - n)) & 0xFF)
    return bytes(out)


class Climate(unittest.TestCase):
    def test_lzw_round_trip(self):
        data = bytes((i * 7 + i // 13) % 256 for i in range(2500)) + b"abababababab" * 50
        self.assertEqual(mc.lzw_decode(lzw_encode(data)), data)

    def test_winkler(self):
        self.assertEqual(mc.winkler_class(2400), "Region I")
        self.assertEqual(mc.winkler_class(3318), "Region III")
        self.assertEqual(mc.winkler_class(4500), "Region V")

    def test_committed_grid(self):
        cl = json.loads((ASSETS / "climate.json").read_text())
        n = cl["grid"]["cols"] * cl["grid"]["rows"]
        for name, layer in cl["layers"].items():
            self.assertEqual(len(layer), n, name)
        v = mc.at(cl, 38.484983, -122.44736)                # Corison: valley floor, St. Helena
        self.assertTrue(700 < v["ppt_mm"] < 1100)
        self.assertTrue(v["tmin_c"] < v["tmean_c"] < v["tmax_c"])
        self.assertIsNone(mc.at(cl, 40.0, -122.44736))


class Vineyards(unittest.TestCase):
    def test_albers_origin(self):
        x, y = mv.albers(23.0, -96.0)                      # EPSG:5070 natural origin
        self.assertAlmostEqual(x, 0, places=3)
        self.assertAlmostEqual(y, 0, places=3)

    def test_committed_drape(self):
        v = json.loads((ASSETS / "vineyards.json").read_text())
        png = (ASSETS / "vineyards.png").read_bytes()
        w, h = struct.unpack(">II", png[16:24])
        self.assertEqual([w, h], v["frame_cells"])
        latest = v["years"][str(v["drape"]["year"])]
        self.assertGreater(latest["ava_acres"]["Napa Valley"], latest["ava_acres"]["St. Helena"])
        self.assertGreater(latest["frame_acres"], latest["ava_acres"]["Napa Valley"])


if __name__ == "__main__":
    unittest.main()
