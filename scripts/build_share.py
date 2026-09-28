"""Build one self-contained HTML file of the viewer for sharing with reviewers (Tier 0, stdlib only).

The viewer normally fetches its data from prototype/assets/, which only works when a web server
serves the repo. This bundles those files into the page itself, so the result opens by double-click
from a download, email attachment or shared drive, and adds a feedback panel (prototype/share/).

    python3 scripts/build_share.py                      # writes dist/terroir-time-machine.html

Data files are embedded as base64 text blocks and served to the page by a small fetch() shim.
Int16 grids (.bin) are delta-coded and byte-split before gzip (about a third smaller); JSON is
gzipped; images are stored as they are. The 3D engine and fonts still load from their CDNs, so
viewers need an internet connection.
"""
import argparse
import array
import base64
import datetime
import gzip
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "prototype" / "timemachine.html"
FEEDBACK = ROOT / "prototype" / "share" / "feedback.html"
OUT = ROOT / "dist" / "terroir-time-machine.html"
# Files the viewer fetches from outside prototype/assets/ (relative to the repo root).
EXTRA = ["SCENES.json", "data/plates/stylized.json"]
# GeoLibre project files are only opened by web.geolibre.app from GitHub, never by the viewer.
SKIP_SUFFIXES = (".geolibre.json",)
MIME = {".json": "application/json", ".bin": "application/octet-stream", ".png": "image/png", ".jpg": "image/jpeg"}
THREE_TAG = '<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>'

SHIM = r"""<script>
/* Shareable build: data files are embedded below and served to the viewer's fetch() calls. */
(function(){
  "use strict";
  const BASE = "https://ttm.local/prototype/timemachine.html";
  const blocks = {};
  document.querySelectorAll('script[type="text/x-ttm"]').forEach(s => { blocks[s.dataset.path] = s; });
  function key(u){
    try { const x = new URL(String(u instanceof Request ? u.url : u), BASE); return x.host === "ttm.local" ? decodeURIComponent(x.pathname.slice(1)) : null; }
    catch (e) { return null; }
  }
  function bytes(s){ const b = atob(s.textContent.trim()), a = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return a; }
  async function gunzip(a){ return new Uint8Array(await new Response(new Blob([a]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer()); }
  function undoInt16(a){
    const n = a.length >> 1, out = new Uint16Array(n); let v = 0;
    for (let i = 0; i < n; i++) { v = (v + (a[i] | (a[n + i] << 8))) & 0xffff; out[i] = v; }
    return new Uint8Array(out.buffer);
  }
  async function body(s){
    const a = bytes(s), enc = s.dataset.enc;
    if (enc === "raw") return a;
    const g = await gunzip(a);
    return enc === "gzi16" ? undoInt16(g) : g;
  }
  const realFetch = window.fetch.bind(window);
  window.fetch = async function(u, opts){
    const k = key(u), s = k && blocks[k];
    if (!s) return k ? new Response("not in this review copy", { status: 404 }) : realFetch(u, opts);
    return new Response(await body(s), { status: 200, headers: { "Content-Type": s.dataset.mime } });
  };
  const urls = {};
  window.__ttmAssetURL = function(u){
    const k = key(u), s = k && blocks[k];
    if (!s || s.dataset.enc !== "raw") return u;
    return urls[k] || (urls[k] = URL.createObjectURL(new Blob([bytes(s)], { type: s.dataset.mime })));
  };
})();
</script>"""

TEXTURE_PATCH = r"""<script>
/* Shareable build: point TextureLoader at the embedded images. */
if (window.THREE) { const load = THREE.TextureLoader.prototype.load; THREE.TextureLoader.prototype.load = function(u, ...a){ return load.call(this, window.__ttmAssetURL(u), ...a); }; }
</script>"""


def encode_int16(raw):
    """Delta along the file, then low bytes followed by high bytes. Inverse of undoInt16 in SHIM."""
    if len(raw) % 2:
        raise ValueError("Int16 grid with an odd byte count")
    v = array.array("H", raw)
    if sys.byteorder != "little":
        v.byteswap()
    d = array.array("H", [0]) * len(v)
    prev = 0
    for i, x in enumerate(v):
        d[i] = (x - prev) & 0xFFFF
        prev = x
    lo = bytes(x & 0xFF for x in d)
    hi = bytes(x >> 8 for x in d)
    return lo + hi


def decode_int16(enc):
    """Python twin of undoInt16, used by the tests."""
    n = len(enc) // 2
    out = array.array("H", [0]) * n
    v = 0
    for i in range(n):
        v = (v + (enc[i] | (enc[n + i] << 8))) & 0xFFFF
        out[i] = v
    if sys.byteorder != "little":
        out.byteswap()
    return out.tobytes()


def pack(path):
    """Return (encoding, bytes) for one file."""
    raw = path.read_bytes()
    if path.suffix == ".bin":
        return "gzi16", gzip.compress(encode_int16(raw), 9, mtime=0)
    if path.suffix in (".png", ".jpg"):
        return "raw", raw
    return "gz", gzip.compress(raw, 9, mtime=0)


def collect(root=ROOT):
    files = [p for p in sorted((root / "prototype" / "assets").rglob("*"))
             if p.is_file() and p.suffix in MIME and not p.name.endswith(SKIP_SUFFIXES)]
    files += [root / e for e in EXTRA if (root / e).exists()]
    return files


def commit_id(root=ROOT):
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True)
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "prototype", "SCENES.json", "data/plates"],
                               capture_output=True, text=True, check=True).stdout.strip()
        return out.stdout.strip() + ("+local" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def build(root=ROOT, out=OUT, built=None):
    html = (root / "prototype" / "timemachine.html").read_text(encoding="utf-8")
    if html.count(THREE_TAG) != 1:
        raise SystemExit("build_share: OrbitControls script tag not found once in timemachine.html")
    commit = commit_id(root)
    built = built or datetime.date.today().isoformat()
    feedback = (root / "prototype" / "share" / "feedback.html").read_text(encoding="utf-8")
    feedback = feedback.replace("__COMMIT__", commit).replace("__BUILT__", built)
    blocks, listing = [], []
    for p in collect(root):
        enc, data = pack(p)
        rel = p.relative_to(root).as_posix()
        blocks.append(f'<script type="text/x-ttm" data-path="{rel}" data-enc="{enc}" data-mime="{MIME[p.suffix]}">'
                      + base64.b64encode(data).decode("ascii") + "</script>")
        listing.append((rel, p.stat().st_size, len(data)))
    head = "<!doctype html>\n" if not html.lstrip().lower().startswith("<!doctype") else ""
    viewport = '<meta name="viewport" content="width=device-width, initial-scale=1">\n' if 'name="viewport"' not in html else ""
    first_script = html.index("<script")
    page = (head + html[:first_script].replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + viewport.rstrip("\n"), 1)
            + "\n".join(blocks) + "\n" + SHIM + "\n" + html[first_script:])
    page = page.replace(THREE_TAG, THREE_TAG + "\n" + TEXTURE_PATCH, 1)
    page = page.replace("<title>Terroir Time Machine</title>", "<title>Terroir Time Machine (review copy)</title>", 1)
    page = page.rstrip() + "\n" + feedback
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out, listing, commit


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    out, listing, commit = build(out=a.out)
    raw = sum(r for _, r, _ in listing)
    size = out.stat().st_size
    print(f"{out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: {size / 1e6:.1f} MB, "
          f"{len(listing)} data files ({raw / 1e6:.1f} MB raw), commit {commit}")
    if size > 25e6:
        print("warning: over 25 MB, too big for most email attachments; share it through a drive link")


if __name__ == "__main__":
    main()
