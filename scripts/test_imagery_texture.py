"""Tier 0 tests for the Sentinel-2 satellite texture (make_imagery_texture.py). No network."""
import json
import struct
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_imagery_texture as mi  # noqa: E402


def item(sq, date, cloud, nodata=0.0):
    return {"id": f"S2A_10S{sq}_{date.replace('-', '')}_0_L2A",
            "properties": {"datetime": date + "T19:00:00Z", "eo:cloud_cover": cloud, "s2:nodata_pixel_percentage": nodata}}


def tiled_tiff(w, h, tw, th, pixel):
    """Classic little-endian tiled RGB TIFF, DEFLATE + horizontal predictor, like the Sentinel-2 TCI COGs."""
    across, down = -(-w // tw), -(-h // th)
    tiles = []
    for ty in range(down):
        for tx in range(across):
            raw = bytearray()
            for r in range(th):
                prev = [0, 0, 0]
                for c in range(tw):
                    px = pixel(tx * tw + c, ty * th + r)
                    raw += bytes((px[k] - prev[k]) & 255 for k in range(3))
                    prev = px
            tiles.append(zlib.compress(bytes(raw)))
    tags = [(256, 3, 1, w), (257, 3, 1, h), (258, 3, 1, 8), (259, 3, 1, 8), (262, 3, 1, 2), (277, 3, 1, 3),
            (284, 3, 1, 1), (317, 3, 1, 2), (322, 3, 1, tw), (323, 3, 1, th)]
    n = len(tags) + 2
    ifd_off = 8
    data_off = ifd_off + 2 + 12 * n + 4
    offs_pos, cnts_pos = data_off, data_off + 4 * len(tiles)
    body_start = cnts_pos + 4 * len(tiles)
    offsets, pos = [], body_start
    for t in tiles:
        offsets.append(pos)
        pos += len(t)
    out = bytearray(b"II*\x00" + struct.pack("<I", ifd_off))
    out += struct.pack("<H", n)
    for tag, typ, cnt, val in tags:
        out += struct.pack("<HHII", tag, typ, cnt, val)
    out += struct.pack("<HHII", 324, 4, len(tiles), offs_pos) if len(tiles) > 1 else struct.pack("<HHII", 324, 4, 1, offsets[0])
    out += struct.pack("<HHII", 325, 4, len(tiles), cnts_pos) if len(tiles) > 1 else struct.pack("<HHII", 325, 4, 1, len(tiles[0]))
    out += struct.pack("<I", 0)
    out += struct.pack(f"<{len(tiles)}I", *offsets) + struct.pack(f"<{len(tiles)}I", *(len(t) for t in tiles))
    for t in tiles:
        out += t
    return bytes(out)


class FakeRemote:
    def __init__(self, blob):
        self.blob = blob

    def __call__(self, url, rng=None, timeout=60):
        return self.blob if rng is None else self.blob[rng[0]:rng[1] + 1]


class ImageryTest(unittest.TestCase):
    def test_mgrs_squares_of_the_frames(self):
        self.assertEqual(mi.mgrs_square(531892, 4280129), "EH")
        self.assertEqual([s for s, _ in mi.squares_for([507900, 4216800, 584100, 4293300])], ["EH"])
        self.assertEqual(mi.squares_for([516892.63, 4265129.75, 546892.63, 4295129.75])[0][1], [499980, 4190220, 609780, 4300020])
        # a frame crossing the 600 km easting line and not covered by one tile needs two squares
        self.assertEqual([s for s, _ in mi.squares_for([590000, 4250000, 640000, 4260000])], ["EH", "FH"])

    def test_pick_scene_prefers_clear_complete_recent(self):
        items = {"EH": [item("EH", "2026-07-14", 0.0), item("EH", "2026-07-20", 0.0, nodata=35.0),
                        item("EH", "2025-08-11", 0.0), item("EH", "2026-08-01", 3.0), item("EH", "2026-06-02", 40.0)]}
        cloud, date, chosen = mi.pick_scene(items, 20)
        self.assertEqual((cloud, date), (0.0, "2026-07-14"))
        with self.assertRaises(SystemExit):
            mi.pick_scene({"EH": [item("EH", "2026-06-02", 40.0)]}, 20)

    def test_pick_scene_needs_the_same_date_for_every_square(self):
        items = {"EH": [item("EH", "2026-07-14", 1.0), item("EH", "2026-07-19", 0.0)],
                 "FH": [item("FH", "2026-07-14", 2.0)]}
        self.assertEqual(mi.pick_scene(items, 20)[1], "2026-07-14")

    def test_reads_a_window_across_tiles(self):
        pixel = lambda x, y: [(x * 7) & 255, (y * 5) & 255, (x + y) & 255]
        blob = tiled_tiff(40, 30, 16, 16, pixel)
        real = mi.http
        mi.http = FakeRemote(blob)
        try:
            f = mi.RangeFile("fake://tci.tif")
            bo, ifds = mi.read_ifds(f)
            win = mi.read_window(f, bo, ifds[0], 10, 12, 20, 9)      # spans 2 x 2 tiles
        finally:
            mi.http = real
        self.assertEqual(len(win), 20 * 9 * 3)
        for r, c in ((0, 0), (3, 7), (8, 19)):
            i = (r * 20 + c) * 3
            self.assertEqual(list(win[i:i + 3]), pixel(10 + c, 12 + r))

    def test_jpeg_is_well_formed(self):
        w, h = 20, 13
        rgb = bytes(v for y in range(h) for x in range(w) for v in (x * 12, y * 19, 255 - x * 12))
        j = mi.encode_jpeg(rgb, w, h, 90)
        self.assertEqual((j[:2], j[-2:]), (b"\xff\xd8", b"\xff\xd9"))
        sof = j.index(b"\xff\xc0")
        self.assertEqual(struct.unpack(">HH", j[sof + 5:sof + 9]), (h, w))
        scan = j[j.index(b"\xff\xda") + 2:-2]
        scan = scan[struct.unpack(">H", scan[:2])[0]:]
        self.assertTrue(all(scan[i + 1] == 0 for i in range(len(scan) - 1) if scan[i] == 0xFF))   # byte stuffing
        for spec in (mi.DC_LUM, mi.DC_CHR, mi.AC_LUM, mi.AC_CHR):
            self.assertEqual(sum(spec[0]), len(spec[1]))

    def test_committed_textures_cover_their_frames(self):
        for folder in (mi.ROOT / "prototype" / "assets", mi.ROOT / "prototype" / "assets" / "regions" / "napa_valley"):
            meta_path = folder / "imagery.json"
            if not meta_path.exists():
                continue
            m = json.loads(meta_path.read_text())
            jpg = (folder / m["image"]["file"]).read_bytes()
            sof = jpg.index(b"\xff\xc0")
            h, w = struct.unpack(">HH", jpg[sof + 5:sof + 9])
            self.assertEqual((w, h), (m["image"]["width"], m["image"]["height"]))
            e0, n0, e1, n1 = m["image"]["bbox_utm"]
            self.assertAlmostEqual((e1 - e0) / w, m["image"]["cell_m"][0], places=2)
            self.assertAlmostEqual((n1 - n0) / h, m["image"]["cell_m"][1], places=2)
            terrain = json.loads((folder / "terrain.json").read_text())["aoi"]["bbox_utm"]
            self.assertEqual([round(v, 2) for v in terrain], [round(v, 2) for v in m["image"]["bbox_utm"]])
            self.assertIn("Copernicus Sentinel data", m["credit"])


if __name__ == "__main__":
    unittest.main()
