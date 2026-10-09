"""Tests for build_site.py (the GitHub Pages _site folder). No network."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_site as bsite  # noqa: E402

ROOT = bsite.ROOT


class SiteBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "_site"
        cls.count, cls.size = bsite.build(cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_root_files_the_pages_fetch_are_found(self):
        paths = bsite.root_paths()
        for p in ("SCENES.json", "data/plates/stylized.json", "data/regions/"):
            self.assertIn(p, paths)

    def test_same_layout_so_up_paths_resolve(self):
        for p in bsite.root_paths():
            self.assertTrue((self.out / p).exists(), p)
        self.assertTrue((self.out / "prototype" / "timemachine.html").is_file())
        self.assertTrue((self.out / "index.html").is_file())
        self.assertIn("prototype/timemachine.html", (self.out / "index.html").read_text())

    def test_every_prototype_file_is_copied(self):
        for src in (ROOT / "prototype").rglob("*"):
            r = src.relative_to(ROOT)
            if src.is_file() and not bsite.excluded(r):
                self.assertTrue((self.out / r).is_file(), r)

    def test_nothing_private_or_bulky(self):
        names = [p.relative_to(self.out) for p in self.out.rglob("*") if p.is_file()]
        for r in names:
            self.assertFalse(bsite.excluded(r), r)
            self.assertNotIn(r.parts[0], {"scripts", "tests", "USGS", ".github", "status"}, r)
        self.assertLess(self.size, 900e6)

    def test_size_limit_fails_the_build(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(SystemExit):
            bsite.build(Path(d) / "s", limit_mb=1)

    def test_exclusions(self):
        for p in ("data/raw/x.tif", "a/.venv/b.py", "notebooks/a.ipynb", "tests/browser/x.mjs", "USGS/a.pdf",
                  "scripts/__pycache__/a.pyc"):
            self.assertTrue(bsite.excluded(Path(p)), p)
        self.assertFalse(bsite.excluded(Path("prototype/assets/terrain.bin")))


if __name__ == "__main__":
    unittest.main()
