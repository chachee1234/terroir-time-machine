#!/usr/bin/env python3
"""Planted vineyards in a region frame from the USDA NASS Cropland Data Layer (CDL, 30 m, class 69 Grapes).

Tier 0, standard library only. For each year, CropScape (nassgeodata.gmu.edu) clips the national CDL to the
frame's envelope in its Albers projection (EPSG:5070) and returns one small GeoTIFF (about 10 MB, 8-bit,
uncompressed). It is cached in data/raw/cdl/ (git-ignored). Each 30 m cell of the region's UTM frame then
takes the CDL class of the Albers cell under its centre, so the counts are for the frame itself, not the
larger envelope CropScape's own statistics would cover.

Output:
  <assets_dir>/vineyards.json   acres of Grapes per year, for the whole frame and inside each AVA polygon
  <assets_dir>/vineyards.png    latest year's Grapes cells on the frame grid (north up, 30 m, transparent
                                elsewhere), for draping on the terrain like geology.png

Limits: the CDL is a satellite classification, not a vineyard survey. Young vines, vineyards under cover crop
and small blocks are missed or labelled as other classes, and some orchards or grass are labelled Grapes.
Treat a single year's acres as an estimate; the change across years is the useful signal.

Rights: USDA NASS Cropland Data Layer, public domain; credit USDA National Agricultural Statistics Service.
SOURCES.md G30.

Usage: make_vineyards.py --region data/regions/napa_valley.json [--years 2012 2016 2020 2024] [--offline]
"""
import argparse
import datetime
import hashlib
import json
import math
import re
import struct
import sys
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_terrain import utm_from_geographic  # noqa: E402
from fetch_tiles import geographic_from_utm  # noqa: E402

API = "https://nassgeodata.gmu.edu/axis2/services/CDLService/GetCDLFile?year={year}&bbox={bbox}"
CACHE = ROOT / "data" / "raw" / "cdl"
GRAPES = 69
CELL = 30.0
ACRES_PER_CELL = CELL * CELL / 4046.8564224
COLOR = (0x70, 0x44, 0x89)            # CDL's own Grapes purple
SOURCE = "USDA NASS Cropland Data Layer (CDL), 30 m, via CropScape (https://nassgeodata.gmu.edu/CropScape/)"
RIGHTS = "Public domain (USDA). Credit: USDA National Agricultural Statistics Service Cropland Data Layer."


def albers(lat, lon):
    """NAD83 / CONUS Albers Equal Area (EPSG:5070) forward, metres."""
    a, f = 6378137.0, 1 / 298.257222101
    e2 = 2 * f - f * f
    e = math.sqrt(e2)
    p1, p2, p0, l0 = map(math.radians, (29.5, 45.5, 23.0, -96.0))
    m = lambda p: math.cos(p) / math.sqrt(1 - e2 * math.sin(p) ** 2)
    q = lambda p: (1 - e2) * (math.sin(p) / (1 - e2 * math.sin(p) ** 2)
                              - math.log((1 - e * math.sin(p)) / (1 + e * math.sin(p))) / (2 * e))
    n = (m(p1) ** 2 - m(p2) ** 2) / (q(p2) - q(p1))
    C = m(p1) ** 2 + n * q(p1)
    rho = lambda p: a * math.sqrt(C - n * q(p)) / n
    th = n * (math.radians(lon) - l0)
    r = rho(math.radians(lat))
    return r * math.sin(th), rho(p0) - r * math.cos(th)


def envelope(region):
    x0, y0, x1, y1 = region["bbox_utm"]
    pts = [albers(*geographic_from_utm(e, n)) for e in (x0, (x0 + x1) / 2, x1) for n in (y0, (y0 + y1) / 2, y1)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return [math.floor(min(xs)) - 60, math.floor(min(ys)) - 60, math.ceil(max(xs)) + 60, math.ceil(max(ys)) + 60]


def fetch(region, year, offline=False):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"cdl_{region['id']}_{year}.tif"
    if not path.exists():
        if offline:
            raise SystemExit(f"{path} missing and --offline set")
        bbox = ",".join(str(v) for v in envelope(region))
        with urllib.request.urlopen(API.format(year=year, bbox=bbox), timeout=300) as r:
            m = re.search(rb"<returnURL>([^<]+)</returnURL>", r.read())
        if not m:
            raise SystemExit(f"CropScape gave no file for {year}")
        print(f"downloading {m.group(1).decode()}", file=sys.stderr)
        with urllib.request.urlopen(m.group(1).decode(), timeout=600) as r:
            path.write_bytes(r.read())
    return path


class Cdl:
    """8-bit, uncompressed, stripped GeoTIFF as CropScape returns it."""

    def __init__(self, data):
        bo = "<" if data[:2] == b"II" else ">"
        off = struct.unpack(bo + "I", data[4:8])[0]
        n = struct.unpack(bo + "H", data[off:off + 2])[0]
        T = {3: "H", 4: "I", 12: "d"}
        tags = {}
        for i in range(n):
            t, ty, c, v = struct.unpack(bo + "HHII", data[off + 2 + 12 * i: off + 14 + 12 * i])
            if ty not in T:
                continue
            size = struct.calcsize(T[ty]) * c
            raw = data[off + 10 + 12 * i: off + 14 + 12 * i] if size <= 4 else data[v:v + size]
            tags[t] = struct.unpack(bo + T[ty] * c, raw[:size])
        if tags[258][0] != 8 or tags[259][0] != 1:
            raise SystemExit("unexpected CDL TIFF (want 8-bit, uncompressed)")
        self.w, self.h = tags[256][0], tags[257][0]
        self.pix = b"".join(data[o:o + c] for o, c in zip(tags[273], tags[279]))
        sx, sy = tags[33550][:2]
        self.x0, self.y0 = tags[33922][3], tags[33922][4]
        self.sx, self.sy = sx, sy

    def at(self, x, y):
        c, r = int((x - self.x0) / self.sx), int((self.y0 - y) / self.sy)
        return self.pix[r * self.w + c] if 0 <= r < self.h and 0 <= c < self.w else 0


def frame_lookup(region, step=32):
    """Albers (x, y) for every 30 m cell centre of the UTM frame, row by row, north first. Exact on a coarse
    lattice, bilinear in between (error well under a metre at this size)."""
    x0, y0, x1, y1 = region["bbox_utm"]
    cols, rows = int(round((x1 - x0) / CELL)), int(round((y1 - y0) / CELL))
    lat_c = list(range(0, cols + step, step))
    lat_r = list(range(0, rows + step, step))
    lattice = {(r, c): albers(*geographic_from_utm(x0 + (c + 0.5) * CELL, y1 - (r + 0.5) * CELL))
               for r in lat_r for c in lat_c}

    def row(r):
        ra = r // step * step
        rb, t = ra + step, (r - ra) / step
        out = []
        for c in range(cols):
            ca = c // step * step
            cb, u = ca + step, (c - ca) / step
            p = [lattice[k] for k in ((ra, ca), (ra, cb), (rb, ca), (rb, cb))]
            out.append(tuple((1 - t) * ((1 - u) * p[0][i] + u * p[1][i]) + t * ((1 - u) * p[2][i] + u * p[3][i])
                             for i in range(2)))
        return out
    return cols, rows, row


def ava_masks(region, cols, rows):
    """{name: set of cell indices} for each AVA polygon, by even-odd scanline fill on the frame grid."""
    x0, y0, x1, y1 = region["bbox_utm"]
    out = {}
    for f in json.loads((ROOT / region["boundary"]).read_text())["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        edges = []
        for poly in polys:
            for ring in poly:
                pts = [utm_from_geographic(lat, lon) for lon, lat in ring]
                pts = [((e - x0) / CELL - 0.5, (y1 - n) / CELL - 0.5) for e, n in pts]
                edges += [(p, q) for p, q in zip(pts, pts[1:]) if p[1] != q[1]]
        cells = set()
        for r in range(rows):
            xs = sorted(p[0] + (r - p[1]) * (q[0] - p[0]) / (q[1] - p[1])
                        for p, q in edges if min(p[1], q[1]) <= r < max(p[1], q[1]))
            for a, b in zip(xs[::2], xs[1::2]):
                for c in range(max(0, math.ceil(a)), min(cols, math.floor(b) + 1)):
                    cells.add(r * cols + c)
        out[f["properties"]["name"].strip()] = cells
    return out


def write_png(path, w, h, mask):
    """Paletted PNG: index 1 = Grapes (CDL purple), index 0 transparent."""
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    raw = bytearray()
    for r in range(h):
        raw.append(0)
        raw += mask[r * w:(r + 1) * w]
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0))
                     + chunk(b"PLTE", bytes((0, 0, 0) + COLOR)) + chunk(b"tRNS", bytes((0, 255)))
                     + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def build(region_path, years, offline=False):
    region = json.loads(Path(region_path).read_text())
    assets = ROOT / region["assets_dir"]
    cols, rows, lookup = frame_lookup(region)
    coords = [lookup(r) for r in range(rows)]
    avas = ava_masks(region, cols, rows)
    out = {"source": SOURCE, "rights": RIGHTS, "built": datetime.date.today().isoformat(),
           "class": "CDL 69 Grapes", "cell_m": CELL, "frame_cells": [cols, rows],
           "limits": "Satellite classification, not a vineyard survey: young vines and small blocks are missed, "
                     "some other crops are labelled Grapes. Read single-year acres as estimates.",
           "years": {}, "files": {}}
    latest = None
    for year in sorted(years):
        path = fetch(region, year, offline)
        cdl = Cdl(path.read_bytes())
        mask = bytearray(cols * rows)
        for r in range(rows):
            base = r * cols
            for c, (x, y) in enumerate(coords[r]):
                if cdl.at(x, y) == GRAPES:
                    mask[base + c] = 1
        total = sum(mask)
        by_ava = {name: round(sum(mask[i] for i in cells) * ACRES_PER_CELL) for name, cells in avas.items()}
        out["years"][str(year)] = {"frame_acres": round(total * ACRES_PER_CELL),
                                   "ava_acres": dict(sorted(by_ava.items(), key=lambda kv: -kv[1]))}
        out["files"][str(year)] = {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        latest = (year, mask)
        print(f"{year}: {out['years'][str(year)]['frame_acres']} acres of Grapes in the frame", file=sys.stderr)
    year, mask = latest
    write_png(assets / "vineyards.png", cols, rows, mask)
    out["drape"] = {"file": "vineyards.png", "year": year, "bbox_utm": region["bbox_utm"], "epsg": region["epsg"]}
    (assets / "vineyards.json").write_text(json.dumps(out, indent=1) + "\n")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2012, 2016, 2020, 2024])
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    out = build(a.region, a.years, a.offline)
    for y, v in out["years"].items():
        top = ", ".join(f"{k} {n}" for k, n in list(v["ava_acres"].items())[:4])
        print(f"{y}: frame {v['frame_acres']} acres; {top}")


if __name__ == "__main__":
    main()
