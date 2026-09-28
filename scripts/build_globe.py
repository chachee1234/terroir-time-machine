#!/usr/bin/env python3
"""Assets for the MVP globe (prototype/globe.html): Earth relief, California relief, California AVAs.

Tier 0, stdlib only. Terrain comes from the AWS Open Data Terrain Tiles (Terrarium PNGs, same source
and cache as fetch_tiles.py); AVA outlines from the UC Davis AVA Project (CC0). Outputs:

  prototype/assets/globe/relief.png      4096 x 2048 equirectangular elevation, 8-bit (see relief.json)
  prototype/assets/globe/california.bin  Int16 metres on a 0.02 degree lat/lon grid, row 0 = north
  prototype/assets/globe/california.json grid metadata and provenance
  prototype/assets/globe/ca_avas.json    current California AVAs, simplified to ~200 m, [lon, lat]
  data/manifest.json                     one entry for the globe assets

Usage: build_globe.py [--ava-file PATH] [--offline]
"""
import argparse
import datetime
import hashlib
import json
import math
import struct
import subprocess
import zlib
from array import array
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_tiles import Mosaic, RIGHTS, TEMPLATE, merc_px  # noqa: E402
from ava_extract import URL as AVA_URL, rings, simplify  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "prototype" / "assets" / "globe"
AVA_CACHE = ROOT / "data" / "raw" / "ava" / "avas.geojson"
CA_BOX = (-124.6, 32.4, -114.0, 42.1)   # lon0, lat0, lon1, lat1
CA_CELL = 0.02                           # degrees
MAX_LAT = 85.05                          # Web Mercator limit
LAND_MAX, SEA_MAX = 8848.0, 11000.0


def encode(h):
    """Elevation (m) to 8 bits: 128..255 land on a square-root scale, 127..0 sea depth likewise."""
    if h >= 0:
        return 128 + round(127 * math.sqrt(min(h, LAND_MAX) / LAND_MAX))
    return 127 - round(127 * math.sqrt(min(-h, SEA_MAX) / SEA_MAX))


def write_png_gray(path, w, h, rows):
    raw = bytearray()
    for r in rows:
        raw.append(1)                                     # Sub filter
        prev = 0
        for v in r:
            raw.append((v - prev) & 255)
            prev = v
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def tiles_for_lonlat(box, z):
    x0, y1 = merc_px(box[1], box[0], z)
    x1, y0 = merc_px(box[3], box[2], z)
    return [(tx, ty) for tx in range(int(x0) // 256, int(x1) // 256 + 1) for ty in range(int(y0) // 256, int(y1) // 256 + 1)]


def earth(offline, w=2048, h=1024, z=3):
    mos = Mosaic(z, offline)
    n = 2 ** z
    mos.prefetch([(x, y) for x in range(n) for y in range(n)])
    size = 256 * n
    rows = []
    for j in range(h):
        lat = max(-MAX_LAT, min(MAX_LAT, 90 - (j + 0.5) * 180 / h))
        row = []
        for i in range(w):
            lon = -180 + (i + 0.5) * 360 / w
            x, y = merc_px(lat, lon, z)
            # wrap longitude, clamp latitude, bilinear
            x, y = x - 0.5, min(size - 1.001, max(0.0, y - 0.5))
            x0, y0 = int(math.floor(x)), int(math.floor(y))
            fx, fy = x - x0, y - y0
            px = lambda gx, gy: mos.px(gx % size, gy)
            v = (px(x0, y0) * (1 - fx) + px(x0 + 1, y0) * fx) * (1 - fy) + (px(x0, y0 + 1) * (1 - fx) + px(x0 + 1, y0 + 1) * fx) * fy
            row.append(encode(v))
        rows.append(row)
    write_png_gray(OUT / "relief.png", w, h, rows)
    meta = {"product": "Earth relief for the globe", "source": "AWS Open Data Terrain Tiles, Terrarium encoding",
            "tile_template": TEMPLATE, "zoom": z, "rights": RIGHTS, "projection": "equirectangular, WGS84; row 0 = 90N",
            "width": w, "height": h, "clamped_lat": MAX_LAT,
            "encoding": "8-bit gray; v>=128: h = ((v-128)/127)^2 * 8848 m; v<128: h = -((127-v)/127)^2 * 11000 m"}
    (OUT / "relief.json").write_text(json.dumps(meta, indent=1) + "\n")
    return mos


def california(offline, z=8):
    mos = Mosaic(z, offline)
    mos.prefetch(tiles_for_lonlat(CA_BOX, z))
    cols = round((CA_BOX[2] - CA_BOX[0]) / CA_CELL) + 1
    rows = round((CA_BOX[3] - CA_BOX[1]) / CA_CELL) + 1
    grid, lo, hi = array("h"), 1e9, -1e9
    for r in range(rows):
        lat = CA_BOX[3] - r * CA_CELL
        for c in range(cols):
            v = mos.sample(lat, CA_BOX[0] + c * CA_CELL)
            lo, hi = min(lo, v), max(hi, v)
            grid.append(max(-32767, min(32767, round(v))))
    if sys.byteorder != "little":
        grid.byteswap()
    data = grid.tobytes()
    (OUT / "california.bin").write_bytes(data)
    meta = {"product": "California relief for the globe", "source": "AWS Open Data Terrain Tiles, Terrarium encoding",
            "tile_template": TEMPLATE, "zoom": z, "rights": RIGHTS, "crs": "WGS84 lat/lon grid",
            "box_lonlat": list(CA_BOX), "cell_deg": CA_CELL, "cols": cols, "rows": rows,
            "encoding": "Int16 little-endian metres, row 0 = north", "range_m": [round(lo, 1), round(hi, 1)],
            "sha256": hashlib.sha256(data).hexdigest()}
    (OUT / "california.json").write_text(json.dumps(meta, indent=1) + "\n")
    return mos


def ca_avas(buf, tol_km=0.2):
    k = math.cos(math.radians(37))
    out = []
    for f in json.loads(buf)["features"]:
        p = f["properties"]
        if p.get("valid_end") or "CA" not in (p.get("state") or "").split("|"):
            continue
        rr = []
        for ring in rings(f["geometry"]):
            xy = [(lon * 111.32 * k, lat * 110.57) for lon, lat, *_ in ring]
            s = simplify(xy, tol_km)
            if len(s) >= 4:
                rr.append([[round(x / (111.32 * k), 4), round(y / 110.57, 4)] for x, y in s])
        if rr:
            out.append({"id": p["ava_id"], "name": p["name"], "within": p.get("within"), "rings": rr})
    out.sort(key=lambda a: a["id"])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ava-file", help="local copy of the UC Davis avas.geojson")
    ap.add_argument("--offline", action="store_true", help="use cached tiles only")
    ap.add_argument("--earth-zoom", type=int, default=4, help="tile zoom for the Earth relief (4 = 256 tiles)")
    ap.add_argument("--earth-width", type=int, default=4096, help="Earth relief width in pixels (height is half)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    if a.ava_file:
        buf = Path(a.ava_file).read_bytes()
    elif AVA_CACHE.exists():
        buf = AVA_CACHE.read_bytes()
    else:
        buf = subprocess.run(["curl", "-sSf", "--max-time", "300", AVA_URL], check=True, capture_output=True).stdout
        AVA_CACHE.parent.mkdir(parents=True, exist_ok=True)
        AVA_CACHE.write_bytes(buf)
    avas = ca_avas(buf)
    (OUT / "ca_avas.json").write_text(json.dumps({"source": "UC Davis Library & DataLab, American Viticultural Areas (AVA) Project",
                                                  "url": AVA_URL, "rights": "CC0 1.0",
                                                  "source_sha256": hashlib.sha256(buf).hexdigest(),
                                                  "simplification_km": 0.2, "avas": avas}, separators=(",", ":")) + "\n")
    print(f"{len(avas)} California AVAs", flush=True)
    m8 = california(a.offline)
    print(f"California grid from {len(m8.files)} z8 tiles", flush=True)
    m3 = earth(a.offline, w=a.earth_width, h=a.earth_width // 2, z=a.earth_zoom)
    print(f"Earth relief from {len(m3.files)} z{a.earth_zoom} tiles", flush=True)

    man_path = ROOT / "data" / "manifest.json"
    man = json.loads(man_path.read_text())
    man["datasets"] = [d for d in man["datasets"] if d.get("id") != "globe-assets"]
    man["datasets"].append({"id": "globe-assets", "source": "AWS Open Data Terrain Tiles (Terrarium) + UC Davis AVA Project",
                            "url_template": TEMPLATE, "ava_url": AVA_URL, "rights": RIGHTS + " AVA outlines: CC0 1.0.",
                            "tiles_sha256": {f"z{a.earth_zoom}": m3.digest(), "z8": m8.digest()},
                            "fetched": datetime.date.today().isoformat(),
                            "derived": [{"file": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                                        for p in sorted(OUT.iterdir()) if p.suffix in (".png", ".bin", ".json")]})
    man_path.write_text(json.dumps(man, indent=2) + "\n")


if __name__ == "__main__":
    main()
