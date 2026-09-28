#!/usr/bin/env python3
"""Rasterize the SIM 2956 geologic map onto the viewer's terrain grid (ROADMAP_CINEMATIC.md Phase 3, step 8).

Input: eswn-geol.e00, the polygon coverage in USGS SIM 2956 (Graymer et al. 2007, DOI 10.3133/sim2956;
digital database package sim2956c.tgz, SHA-256 3d2feff6...). SOURCES.md G07: USGS-produced, public domain in
the U.S., credit USGS. The coverage is NAD27 / UTM zone 10 (metres, Clarke 1866), per STATUS.md M1-05.

Output, on the exact grid of the terrain metadata (default prototype/assets/terrain.json: its
browser_grid cells over aoi.bbox_utm, NAD83 / UTM 10N, row 0 = north, cell-centred):
  prototype/assets/geology.png          RGBA, one colour per PTYPE; transparent outside the mapped area
  prototype/assets/geology_legend.json  PTYPE -> colour and cell count, source, datum note

Method: arcs carry their left and right polygon numbers, so each grid row is scanned once: sort the arc
crossings of the row's centre line by x, and each cell centre takes the polygon on the east side of the
nearest crossing to its west. Polygon 1 is the Arc/INFO universe polygon (outside the map). The NAD27 ->
NAD83 shift is one constant offset for the grid, computed at its centre with the standard three-parameter
CONUS mean transformation (dX -8, dY 160, dZ 176 m; NIMA TR8350.2). That is a ballpark transform (a few
metres), well below the grid's cell size; it is not NADCON (STATUS.md keeps the high-accuracy transform
as a pending check).

Tier 0, standard library only (GDAL is not installed; no dependency added).
Usage: make_geology_texture.py data/raw/eswn-geol.e00                          # the 30 km block (?region=mt_st_helena)
       make_geology_texture.py data/raw/eswn-geol.e00 --terrain prototype/assets/regions/napa_valley/terrain.json \
           --out-dir prototype/assets/regions/napa_valley                     # the default Napa Valley frame
"""
import argparse
import bisect
import colorsys
import hashlib
import json
import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLARKE1866 = (6378206.4, 1 / 294.978698214)
GRS80 = (6378137.0, 1 / 298.257222101)
NAD27_TO_NAD83 = (-8.0, 160.0, 176.0)   # metres, CONUS mean (NIMA TR8350.2, Table B.1)


# ----------------------------------------------------------------------------- E00 reading
def read_e00(path):
    """Arcs and the polygon attribute table from an uncompressed Arc/INFO E00 export."""
    lines = Path(path).read_text(encoding="latin-1").splitlines()
    if not lines or not lines[0].startswith("EXP"):
        raise SystemExit(f"{path}: not an E00 export")
    if lines[0][3:8].strip().startswith("1"):
        raise SystemExit(f"{path}: compressed E00; decompress it first (e.g. with e00conv or avcimport)")
    arcs, pat, i = [], None, 1
    while i < len(lines):
        tag = lines[i][:3]
        if tag == "ARC":
            i, arcs = read_arcs(lines, i)
        elif tag == "IFO":
            i, tables = read_ifo(lines, i)
            pat = next((t for n, t in tables.items() if n.upper().endswith(".PAT")), None)
        else:
            i += 1
    if not arcs:
        raise SystemExit(f"{path}: no ARC section")
    if pat is None:
        raise SystemExit(f"{path}: no polygon attribute table (.PAT)")
    return arcs, pat


def _fixed(line, width):
    return [float(line[k:k + width]) for k in range(0, len(line.rstrip()), width) if line[k:k + width].strip()]


def read_arcs(lines, i):
    """ARC 2 (single precision, two pairs per line) or ARC 3 (double, one pair per line)."""
    double = lines[i][3:].strip().startswith("3")
    width = 21 if double else 14
    arcs, i = [], i + 1
    while True:
        head = [int(lines[i][k:k + 10]) for k in range(0, 70, 10)]
        i += 1
        if head[0] == -1:
            return i, arcs
        n = head[6]
        vals = []
        while len(vals) < 2 * n:
            vals += _fixed(lines[i], width)
            i += 1
        arcs.append({"lpoly": head[4], "rpoly": head[5], "pts": list(zip(vals[0::2], vals[1::2]))})


def read_ifo(lines, i):
    """INFO tables: {name: [record dicts]}; text columns only as far as needed (char, int, float)."""
    tables, i = {}, i + 1
    while not lines[i].startswith("EOI"):
        head = lines[i]
        name = head[:32].strip()
        nfields, nrec = int(head[34:38]), int(head[46:56])
        i += 1
        fields = []
        for _ in range(nfields):
            f = lines[i]
            size, typ, index = int(f[16:19]), int(f[34:37]) // 10, int(f[65:69] or -1)
            i += 1
            if index < 0:          # redefined item: not written in records
                continue
            width = {1: 8, 2: size, 3: size, 4: size, 5: 6 if size == 2 else 11,
                     6: 14 if size == 4 else 24}[typ]
            fields.append((f[:16].strip(), typ, width))
        reclen = sum(w for _, _, w in fields)
        recs = []
        for _ in range(nrec):
            buf = ""
            while len(buf) < reclen:           # records wrap at 80 characters
                buf += lines[i].ljust(80)[:80] if reclen - len(buf) >= 80 else lines[i].ljust(reclen - len(buf))
                i += 1
            rec, k = {}, 0
            for fname, typ, w in fields:
                raw = buf[k:k + w]; k += w
                rec[fname] = raw.strip() if typ in (1, 2) else (float(raw) if typ in (4, 6) else int(raw))
            recs.append(rec)
        tables[name] = recs
    return i + 1, tables


# ----------------------------------------------------------------------------- datum and projection
def _tm_consts(ell):
    a, f = ell
    n = f / (2 - f)
    A = a / (1 + n) * (1 + n**2 / 4 + n**4 / 64)
    al = [n / 2 - 2 * n**2 / 3 + 5 * n**3 / 16, 13 * n**2 / 48 - 3 * n**3 / 5, 61 * n**3 / 240]
    be = [n / 2 - 2 * n**2 / 3 + 37 * n**3 / 96, n**2 / 48 + n**3 / 15, 17 * n**3 / 480]
    de = [2 * n - 2 * n**2 / 3 - 2 * n**3, 7 * n**2 / 3 - 8 * n**3 / 5, 56 * n**3 / 15]
    return n, A, al, be, de


def utm_inverse(e, nn, ell, zone=10):
    n, A, _, be, de = _tm_consts(ell)
    xi, eta = nn / (0.9996 * A), (e - 500000) / (0.9996 * A)
    xp = xi - sum(be[j] * math.sin(2 * (j + 1) * xi) * math.cosh(2 * (j + 1) * eta) for j in range(3))
    ep = eta - sum(be[j] * math.cos(2 * (j + 1) * xi) * math.sinh(2 * (j + 1) * eta) for j in range(3))
    chi = math.asin(math.sin(xp) / math.cosh(ep))
    lat = chi + sum(de[j] * math.sin(2 * (j + 1) * chi) for j in range(3))
    lon = math.radians(zone * 6 - 183) + math.atan2(math.sinh(ep), math.cos(xp))
    return lat, lon


def utm_forward(lat, lon, ell, zone=10):
    n, A, al, _, _ = _tm_consts(ell)
    lam = lon - math.radians(zone * 6 - 183)
    t = math.sinh(math.atanh(math.sin(lat)) - 2 * math.sqrt(n) / (1 + n) * math.atanh(2 * math.sqrt(n) / (1 + n) * math.sin(lat)))
    xp, ep = math.atan2(t, math.cos(lam)), math.atanh(math.sin(lam) / math.sqrt(1 + t * t))
    x = ep + sum(al[j] * math.cos(2 * (j + 1) * xp) * math.sinh(2 * (j + 1) * ep) for j in range(3))
    y = xp + sum(al[j] * math.sin(2 * (j + 1) * xp) * math.cosh(2 * (j + 1) * ep) for j in range(3))
    return 500000 + 0.9996 * A * x, 0.9996 * A * y


def _ecef(lat, lon, ell):
    a, f = ell; e2 = f * (2 - f); N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    return (N * math.cos(lat) * math.cos(lon), N * math.cos(lat) * math.sin(lon), N * (1 - e2) * math.sin(lat))


def _geodetic(x, y, z, ell):
    a, f = ell; e2 = f * (2 - f); p = math.hypot(x, y); lat = math.atan2(z, p * (1 - e2))
    for _ in range(6):
        N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2); lat = math.atan2(z + e2 * N * math.sin(lat), p)
    return lat, math.atan2(y, x)


def nad83_to_nad27_offset(e83, n83):
    """(dE, dN) to add to NAD83 UTM 10 metres to get NAD27 UTM 10 metres, near one point."""
    lat, lon = utm_inverse(e83, n83, GRS80)
    x, y, z = _ecef(lat, lon, GRS80)
    lat27, lon27 = _geodetic(x - NAD27_TO_NAD83[0], y - NAD27_TO_NAD83[1], z - NAD27_TO_NAD83[2], CLARKE1866)
    e27, n27 = utm_forward(lat27, lon27, CLARKE1866)
    return e27 - e83, n27 - n83


# ----------------------------------------------------------------------------- rasterizing
def rasterize(arcs, x0, y1, cell, cols, rows, cell_y=None):
    """Polygon number at each cell centre (0 = no crossing to the west, i.e. outside every arc)."""
    cy = cell_y or cell
    segs = [(a["pts"][k], a["pts"][k + 1], a["lpoly"], a["rpoly"]) for a in arcs for k in range(len(a["pts"]) - 1)]
    rows_x = [[] for _ in range(rows)]
    for (ax, ay), (bx, by), lp, rp in segs:
        if ay == by:
            continue
        lo, hi = min(ay, by), max(ay, by)
        r0 = max(0, math.ceil((y1 - hi) / cy - 0.5)); r1 = min(rows - 1, math.floor((y1 - lo) / cy - 0.5))
        east = rp if by > ay else lp          # walking north, the right-hand polygon is to the east
        for r in range(r0, r1 + 1):
            yc = y1 - (r + 0.5) * cy
            if lo <= yc < hi:
                rows_x[r].append((ax + (yc - ay) * (bx - ax) / (by - ay), east))
    grid = []
    for r in range(rows):
        xs = sorted(rows_x[r]); keys = [c[0] for c in xs]
        row = []
        for c in range(cols):
            k = bisect.bisect_right(keys, x0 + (c + 0.5) * cell) - 1
            row.append(xs[k][1] if k >= 0 else 0)
        grid.append(row)
    return grid


def palette(ptypes):
    """One colour per unit code: golden-angle hues over the sorted codes (neighbours in the list get far-apart
    hues), lightness and saturation cycling, muted like a printed geologic map. Same codes, same colours."""
    out = {}
    for i, t in enumerate(sorted(ptypes)):
        r, g, b = colorsys.hls_to_rgb((i * 0.381966) % 1.0, (0.50, 0.62, 0.42)[i % 3], (0.45, 0.60, 0.35)[(i // 3) % 3])
        out[t] = "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))
    return out


def write_png(path, rgba, w, h):
    raw = b"".join(b"\x00" + bytes(rgba[r * w * 4:(r + 1) * w * 4]) for r in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def terrain_grid(meta):
    """(x0, y1, cell_x, cell_y, cols, rows): the browser grid's cells spread over the bbox, as the viewer draws it."""
    x0, y0, x1, y1 = meta["aoi"]["bbox_utm"]
    g = meta["browser_grid"]
    cols, rows = g.get("cols", g.get("cells")), g.get("rows", g.get("cells"))
    cx, cy = (x1 - x0) / cols, (y1 - y0) / rows
    if abs(cx / g["cell_m"] - 1) > 0.002 or abs(cy / g["cell_m"] - 1) > 0.002:
        raise SystemExit("terrain grid does not match its bbox (cells x cell_m should equal the bbox size)")
    return x0, y1, cx, cy, cols, rows


def _rel(path):
    p = Path(path).resolve()
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name


def build(e00, terrain, out_dir):
    meta = json.loads(Path(terrain).read_text())
    x0, y1, cell, cell_y, cols, rows = terrain_grid(meta)
    arcs, pat = read_e00(e00)
    if not pat or "PTYPE" not in pat[0]:
        raise SystemExit("polygon table has no PTYPE field")
    cx, cy = x0 + cols * cell / 2, y1 - rows * cell_y / 2
    de, dn = nad83_to_nad27_offset(cx, cy)
    poly = rasterize(arcs, x0 + de, y1 + dn, cell, cols, rows, cell_y)     # grid moved into the map's NAD27 frame
    ptype = lambda p: pat[p - 1]["PTYPE"] if 1 < p <= len(pat) else ""
    counts = {}
    for row in poly:
        for p in row:
            t = ptype(p)
            if t:
                counts[t] = counts.get(t, 0) + 1
    cols_hex = palette(counts)
    rgba = bytearray(cols * rows * 4)
    for r, row in enumerate(poly):
        for c, p in enumerate(row):
            t = ptype(p)
            if t:
                h = cols_hex[t]
                rgba[(r * cols + c) * 4:(r * cols + c + 1) * 4] = bytes((int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    write_png(out / "geology.png", rgba, cols, rows)
    legend = {"label": "USGS SIM 2956, 1:100,000",
              "source": "Graymer, R.W., et al., 2007, Geologic Map and Map Database of Eastern Sonoma and Western Napa "
                        "Counties, California: USGS Scientific Investigations Map 2956, DOI 10.3133/sim2956",
              "rights": "USGS-produced, public domain in the U.S.; credit U.S. Geological Survey (SOURCES.md G07)",
              "input": {"file": Path(e00).name, "sha256": hashlib.sha256(Path(e00).read_bytes()).hexdigest(),
                        "arcs": len(arcs), "polygons": len(pat) - 1},
              "grid": {"terrain": _rel(terrain), "cols": cols, "rows": rows, "cell_m": [round(cell, 3), round(cell_y, 3)],
                       "bbox_utm": meta["aoi"]["bbox_utm"], "crs": "NAD83 / UTM 10N, row 0 = north, cell centres sampled"},
              "datum_note": f"Map is NAD27 / UTM 10 (Clarke 1866). Grid shifted by a constant dE {de:.1f} m, dN {dn:.1f} m "
                            "(three-parameter CONUS mean, NIMA TR8350.2), not NADCON.",
              "limits": "Published at 1:100,000. Each cell shows the unit at its centre, so units narrower than a cell "
                        "and exact contact positions are not resolved. Transparent cells are outside the mapped area.",
              "units": [{"ptype": t, "color": cols_hex[t], "cells": n} for t, n in sorted(counts.items(), key=lambda kv: -kv[1])],
              "unmapped_cells": cols * rows - sum(counts.values())}
    (out / "geology_legend.json").write_text(json.dumps(legend, indent=1) + "\n")
    return legend


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("e00")
    ap.add_argument("--terrain", default=str(ROOT / "prototype" / "assets" / "terrain.json"))
    ap.add_argument("--out-dir", default=str(ROOT / "prototype" / "assets"))
    a = ap.parse_args()
    lg = build(a.e00, a.terrain, a.out_dir)
    print(f"{lg['grid']['cols']}x{lg['grid']['rows']} cells, {len(lg['units'])} units, {lg['unmapped_cells']} unmapped; "
          + ", ".join(f"{u['ptype']} {u['cells']}" for u in lg["units"][:8]))
    print(lg["datum_note"])


if __name__ == "__main__":
    main()
