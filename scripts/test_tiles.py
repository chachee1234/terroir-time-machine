"""Tests for the Terrain Tiles helpers (fetch_tiles.py) and the globe encoding (build_globe.py)."""
import struct
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_terrain import utm_from_geographic  # noqa: E402
from fetch_tiles import decode_png_rgb, geographic_from_utm, grid_shape, merc_px, terrarium_heights  # noqa: E402
from build_globe import encode  # noqa: E402


def png_rgb(w, h, rows, filt=0):
    raw = b"".join(bytes([filt]) + bytes(r) for r in rows)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b"")


class TestTiles(unittest.TestCase):
    def test_utm_round_trip(self):
        for lat, lon in [(38.6691784, -122.6333914), (38.15, -122.06), (36.0, -121.2)]:
            la, lo = geographic_from_utm(*utm_from_geographic(lat, lon))
            self.assertAlmostEqual(la, lat, places=7)
            self.assertAlmostEqual(lo, lon, places=7)

    def test_merc_px(self):
        self.assertEqual(merc_px(0, 0, 0), (128.0, 128.0))
        x, y = merc_px(0, -180, 3)
        self.assertAlmostEqual(x, 0.0)

    def test_terrarium_decode(self):
        # 0 m is (128, 0, 0); 1317.5 m is (133, 37, 128); -10 m is (127, 246, 0)
        rows = [[128, 0, 0, 133, 37, 128], [127, 246, 0, 128, 0, 0]]
        h = terrarium_heights(png_rgb(2, 2, rows))
        self.assertEqual(list(h), [0.0, 1317.5, -10.0, 0.0])

    def test_png_filters(self):
        rows = [[10, 20, 30, 40, 50, 60], [1, 2, 3, 4, 5, 6]]
        self.assertEqual(list(decode_png_rgb(png_rgb(2, 2, rows, 0))[3]), sum(rows, []))
        sub = [[10, 20, 30, 30, 30, 30], [1, 2, 3, 3, 3, 3]]          # Sub filter: differences from the pixel to the left
        self.assertEqual(list(decode_png_rgb(png_rgb(2, 2, sub, 1))[3]), sum(rows, []))

    def test_grid_shape(self):
        self.assertEqual(grid_shape([0, 0, 10000, 5000], cell=15, max_cells=512), (512, 256))  # capped at 512 cells on the long side
        self.assertEqual(grid_shape([0, 0, 3000, 3000], cell=15, max_cells=512), (201, 201))

    def test_globe_encoding(self):
        self.assertEqual(encode(0), 128)
        self.assertEqual(encode(8848), 255)
        self.assertEqual(encode(-11000), 0)
        self.assertTrue(encode(-1) <= 127)

    def test_frame_grid_block_means_match_the_region_request(self):
        import fetch_tiles as ft
        from fetch_terrain import region_request

        class Tilt:                                   # elevation = metres east of the frame's west edge / 100
            def sample(self, lat, lon):
                return (ft.utm_from_geographic(lat, lon)[0] - 540000) / 100
        region = {"bbox_utm": [540000, 4250000, 543000, 4251500], "cell_m": 30, "browser_cells": 20}
        w, h, nx, ny = region_request(region)
        self.assertEqual((w, h, nx, ny), (100, 50, 20, 10))
        grid, lo, hi, at = ft.block_mean_grid(Tilt(), region["bbox_utm"], w, h, nx, ny)
        self.assertEqual(len(grid), nx * ny)
        self.assertAlmostEqual(grid[0], 0.75, delta=1)                   # first block: mean of 15..135 m east
        self.assertAlmostEqual(grid[nx - 1], 29, delta=1)                  # last block: ~2925 m east
        self.assertLess(abs(at[0] - 542985), 1)                            # highest sample in the east column


if __name__ == "__main__":
    unittest.main()
