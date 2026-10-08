"""Tier 0 tests for security_check.py: the repo passes, and each check catches a seeded problem."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import net  # noqa: E402
import security_check as sc  # noqa: E402


def tree(files):
    d = tempfile.TemporaryDirectory()
    root = Path(d.name)
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    return d, root


GOOD_WF = """name: ok
on: [push]
permissions:
  contents: read
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7
      - env:
          TITLE: ${{ github.event.issue.title }}
        run: |
          echo "$TITLE"
"""


class RepoPasses(unittest.TestCase):
    def test_repo_has_no_findings(self):
        self.assertEqual({k: v for k, v in sc.run().items() if v}, {})


class Seeded(unittest.TestCase):
    def test_secrets(self):
        d, root = tree({"a.py": 'KEY = "AKIA' + "ABCDEFGHIJKLMNOP" + '"\n', "b.md": "ghp_" + "a" * 36})
        with d:
            sc.ROOT, old = root, sc.ROOT
            try:
                found = sc.check_secrets([root / "a.py", root / "b.md"])
            finally:
                sc.ROOT = old
        self.assertEqual(len(found), 2)

    def test_workflows(self):
        bad = GOOD_WF.replace("permissions:\n  contents: read\n", "").replace(
            "@3d3c42e5aac5ba805825da76410c181273ba90b1", "@v4").replace('echo "$TITLE"', 'echo "${{ github.event.issue.title }}"')
        bad = bad.replace("on: [push]", "on:\n  pull_request_target:")
        d, root = tree({".github/workflows/good.yml": GOOD_WF, ".github/workflows/bad.yml": bad})
        with d:
            found = sc.check_workflows(root)
        self.assertTrue(all(f.startswith(".github/workflows/bad.yml") for f in found), found)
        for what in ("permissions", "pull_request_target", "not pinned", "inside a run: script"):
            self.assertTrue(any(what in f for f in found), what)

    def test_inline_run_is_checked(self):
        d, root = tree({".github/workflows/x.yml": GOOD_WF + "      - run: echo ${{ github.head_ref }}\n"})
        with d:
            self.assertEqual(len(sc.check_workflows(root)), 1)

    def test_pages(self):
        html = ('<script src="https://evil.test/x.js"></script><script src="https://cdnjs.cloudflare.com/a.js"></script>'
                '<a href="x" target="_blank">x</a>\n<script>eval("1")</script>')
        d, root = tree({"prototype/p.html": html})
        with d:
            found = sc.check_pages(root)
        self.assertEqual(len(found), 5, found)   # unlisted host, 2 x no SRI, no noopener, eval

    def test_scripts(self):
        py = ("import subprocess\nsubprocess.run('x', shell=True)\nz.extractall(d)\nyaml.load(f)\n"
              "urllib.request.urlopen(u)\nok = 1  # eval( in a comment\n")
        d, root = tree({"scripts/x.py": py, "scripts/test_x.py": py})
        with d:
            found = sc.check_scripts(root)
        self.assertEqual(len(found), 4, found)

    def test_sri_digest(self):
        self.assertTrue(sc.sri_matches(b"alert(1)", "sha384", "HT2E9NfWiuQ/w1PRai+hTyqW16NIoCGA/m8VQDUopfAtcz6YQjtsMmQd5uRbVDpW"))
        self.assertFalse(sc.sri_matches(b"alert(2)", "sha384", "HT2E9NfWiuQ/w1PRai+hTyqW16NIoCGA/m8VQDUopfAtcz6YQjtsMmQd5uRbVDpW"))


class OpenUrl(unittest.TestCase):
    def test_only_http_schemes(self):
        import urllib.request
        for bad in ("file:///etc/passwd", "ftp://example.com/x", urllib.request.Request("file:///etc/hosts")):
            with self.subTest(url=bad), self.assertRaises(ValueError):
                net.open_url(bad, timeout=1)


if __name__ == "__main__":
    unittest.main()
