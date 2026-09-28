"""Tier 0 tests for the shareable single-file build (build_share.py). No network, no browser."""
import base64
import gzip
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_share as bs  # noqa: E402


class ShareBuildTest(unittest.TestCase):
    def test_int16_coding_round_trips(self):
        raw = bytes([0x00, 0x80, 0xFF, 0x7F, 0x01, 0x00, 0xFE, 0xFF, 0x34, 0x12])   # -32768, 32767, 1, -2, 4660
        self.assertEqual(bs.decode_int16(bs.encode_int16(raw)), raw)
        grid = (bs.ROOT / "prototype" / "assets" / "terrain.bin")
        if grid.exists():
            b = grid.read_bytes()
            self.assertEqual(bs.decode_int16(bs.encode_int16(b)), b)
        with self.assertRaises(ValueError):
            bs.encode_int16(b"\x01\x02\x03")

    def test_every_fetched_path_is_embedded(self):
        page = (bs.ROOT / "prototype" / "timemachine.html").read_text(encoding="utf-8")
        embedded = {p.relative_to(bs.ROOT).as_posix() for p in bs.collect()}
        literal = set(re.findall(r'(?:fetch|\.load)\("([^"+]+\.(?:json|bin|png|jpg))"', page))
        self.assertTrue(literal)
        for u in literal:
            path = os.path.normpath(os.path.join("prototype", u)).replace(os.sep, "/")
            self.assertIn(path, embedded, u)
        self.assertFalse([p for p in embedded if p.endswith(".geolibre.json")])

    def test_built_page_is_self_contained(self):
        with tempfile.TemporaryDirectory() as d:
            out, listing, _ = bs.build(out=Path(d) / "share.html", built="2026-01-01")
            html = out.read_text(encoding="utf-8")
        self.assertEqual(len(listing), len(bs.collect()))
        blocks = re.findall(r'<script type="text/x-ttm" data-path="([^"]+)" data-enc="(\w+)" data-mime="[^"]+">([^<]+)</script>', html)
        self.assertEqual(len(blocks), len(listing))
        by_path = {p: (e, d) for p, e, d in blocks}
        e, data = by_path["SCENES.json"]
        self.assertEqual(e, "gz")
        self.assertEqual(gzip.decompress(base64.b64decode(data)), (bs.ROOT / "SCENES.json").read_bytes())
        for p, (e, data) in by_path.items():
            if e == "gzi16":
                self.assertEqual(bs.decode_int16(gzip.decompress(base64.b64decode(data))), (bs.ROOT / p).read_bytes(), p)
                break
        # data blocks and the fetch shim come before the viewer script; the texture patch follows three.js
        self.assertLess(html.index('type="text/x-ttm"'), html.index("window.fetch = async"))
        self.assertLess(html.index("window.fetch = async"), html.index("cdnjs.cloudflare.com/ajax/libs/three.js"))
        self.assertLess(html.index(bs.THREE_TAG), html.index("TextureLoader.prototype.load = function"))
        self.assertIn('id="fbBtn"', html)
        self.assertIn("built 2026-01-01", html)
        self.assertNotIn("__COMMIT__", html)
        self.assertIn("(review copy)</title>", html)


if __name__ == "__main__":
    unittest.main()
