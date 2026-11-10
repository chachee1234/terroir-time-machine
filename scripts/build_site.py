"""Build the GitHub Pages site into _site/ (used by .github/workflows/pages.yml; stdlib only, no network).

The pages in prototype/ fetch a few files from the repository root with ../ paths (SCENES.json,
data/plates/..., data/regions/...). The site keeps the repository's layout, so those paths work unchanged:

  _site/index.html          redirect to prototype/timemachine.html (copied from the repository root)
  _site/prototype/...       every file in prototype/
  _site/<root files>        each ../ path found in prototype/*.html, plus the licence files

Never copied: data/raw/, .venv, notebooks, tests, USGS/ source archives, caches. The build fails when _site
is larger than the limit (GitHub Pages sites may be at most 1 GB).

  python3 scripts/build_site.py [--out _site] [--limit-mb 900]
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRA = ["index.html", "LICENSE", "LICENSE-CONTENT.md"]
# path parts that never go on the site, wherever they appear
EXCLUDE_PARTS = {"raw", ".venv", "venv", "notebooks", "tests", "USGS", "__pycache__", "node_modules", ".git",
                 ".ipynb_checkpoints", ".DS_Store"}
EXCLUDE_SUFFIXES = {".pyc", ".ipynb", ".zip", ".tar", ".gz", ".tgz", ".7z"}
UP_PATH = re.compile(r'''["'`]\.\./([A-Za-z0-9_./-]+)''')


def root_paths(root=ROOT):
    """Repository-root files and folders the pages fetch with ../ paths, as sorted relative strings."""
    found = set()
    for page in (root / "prototype").rglob("*.html"):
        for p in UP_PATH.findall(page.read_text(encoding="utf-8")):
            if ".." in p.split("/"):
                raise SystemExit(f"{page.relative_to(root)}: path climbs above the repository: ../{p}")
            found.add(p)
    return sorted(found)


def excluded(rel):
    return bool(EXCLUDE_PARTS.intersection(rel.parts)) or rel.suffix.lower() in EXCLUDE_SUFFIXES


def files_for(rel, root=ROOT):
    src = root / rel
    if src.is_file():
        return [src]
    if src.is_dir():
        return sorted(p for p in src.rglob("*") if p.is_file())
    raise SystemExit(f"a page fetches ../{rel}, which is not in the repository")


def build(out, root=ROOT, limit_mb=900):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    wanted = ["prototype"] + root_paths(root) + [p for p in EXTRA if (root / p).exists()]
    copied, total = 0, 0
    for rel in wanted:
        for src in files_for(rel, root):
            r = src.relative_to(root)
            if excluded(r):
                continue
            dst = out / r
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
            total += src.stat().st_size
    (out / ".nojekyll").write_text("")
    mb = total / 1e6
    print(f"{out}: {copied} files, {mb:.1f} MB (limit {limit_mb} MB)")
    print("root files fetched by the pages: " + ", ".join(root_paths(root)))
    if mb > limit_mb:
        raise SystemExit(f"{out} is {mb:.1f} MB, over the {limit_mb} MB limit")
    return copied, total


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "_site"))
    ap.add_argument("--limit-mb", type=float, default=900)
    a = ap.parse_args()
    build(a.out, limit_mb=a.limit_mb)


if __name__ == "__main__":
    sys.exit(main())
