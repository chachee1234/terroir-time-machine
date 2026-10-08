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

# Files the viewer fetches whose data lands in a separate PR (code first, data after). Once the file
# is committed it must be embedded like any other; remove it from here when that happens.
PENDING_DATA = {"prototype/assets/regions/napa_valley/daily/index.json"}   # PRISM daily, PR #43 follow-up


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
            if path in PENDING_DATA and not (bs.ROOT / path).exists():
                # built by a later data step; until then the viewer must treat it as absent, not crash
                self.assertIn(f'fetch("{u}").then(r=>{{ if(!r.ok) throw 0;', page, u)
                continue
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

    def test_location_pages_get_their_own_file(self):
        napa = {p.relative_to(bs.ROOT).as_posix() for p in bs.collect()}
        self.assertFalse([p for p in napa if p.startswith("prototype/assets/locations/")])
        gib = {p.relative_to(bs.ROOT).as_posix() for p in bs.collect(page="gibraltar")}
        self.assertIn("prototype/assets/locations/gibraltar/terrain.json", gib)
        self.assertTrue(all(p.startswith("prototype/assets/locations/gibraltar/") for p in gib))
        with tempfile.TemporaryDirectory() as d:
            out, listing, _ = bs.build(out=Path(d) / "g.html", built="2026-01-01", page="gibraltar")
            html = out.read_text(encoding="utf-8")
            napa_out, _, _ = bs.build(out=Path(d) / "n.html", built="2026-01-01")
            napa_html = napa_out.read_text(encoding="utf-8")
        self.assertEqual(len(listing), len(gib))
        self.assertIn('https://ttm.local/prototype/gibraltar.html', html)
        self.assertIn('href="terroir-time-machine.html"', html)          # the Napa link points at the other review copy
        self.assertIn('href="terroir-time-machine-gibraltar.html"', napa_html)
        self.assertIn("(review copy)</title>", html)


if __name__ == "__main__":
    unittest.main()
