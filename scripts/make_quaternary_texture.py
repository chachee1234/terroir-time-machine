#!/usr/bin/env python3
"""Young deposits at 1:24,000 on the close-ups: USGS Open-File Report 2006-1037 over SIM 2956.

Witter, R.C., et al., 2006, Maps of Quaternary Deposits and Liquefaction Susceptibility in the Central San Francisco
Bay Region, California: USGS Open-File Report 2006-1037 (https://pubs.usgs.gov/of/2006/1037/). Public domain (USGS).
Its Quaternary units (fans, terraces, stream channels, basin deposits, by age) were mapped at 1:24,000 from
landforms and soils; everything older is one unit, "br" (pre-Quaternary deposits and bedrock). The map reaches
north to 38.625 N, so it covers the Napa Valley floor up to just north of Calistoga, Carneros and the Sonoma Valley.

For each close-up in <out-dir>/detail/index.json this redraws detail/<id>.geology.png: the SIM 2956 map
(1:100,000, as make_geology_texture.py --closeups draws it), with every 1:24,000 Quaternary polygon drawn on top.
Where the finer map says "br", or the close-up is outside it, the SIM 2956 unit stays, so hills keep their bedrock
units. detail/geology.json then lists each unit with the map it came from. A unit code found on both maps (Qhf,
Qhc ...) keeps one colour; the two maps use the same code system (Knudsen et al. 2000 and its successors).

Input: of06-1037_4b.shp.zip (the shapefile package, read in place, not extracted) and of06-1037_9.meta.txt (unit
names). The shapefile is in geographic coordinates on NAD27; the NAD27 -> NAD83 shift is the same constant
offset per close-up as make_geology_texture.py uses.

Tier 0, standard library only.
Usage: make_quaternary_texture.py data/raw/eswn-geol.e00 --zip data/raw/of06-1037_4b.shp.zip \
           --meta data/raw/of06-1037_9.meta.txt --out-dir prototype/assets/regions/napa_valley
"""
import argparse
import hashlib
import json
import math
import re
import struct
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_geology_texture as mg  # noqa: E402
from make_rivers import read_dbf  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ("Witter, R.C., Knudsen, K.L., Sowers, J.M., Wentworth, C.M., Koehler, R.D., and Randolph, C.E., 2006, "
          "Maps of Quaternary Deposits and Liquefaction Susceptibility in the Central San Francisco Bay Region, "
          "California: USGS Open-File Report 2006-1037, https://pubs.usgs.gov/of/2006/1037/")
FALLBACK = {"br"}          # the finer map's "older rock": keep the SIM 2956 unit
RENAME = {"H2O": "water"}  # the finer map's code for open water, as SIM 2956 calls it


def read_polygons(data):
    """(bbox, rings) of each record of a Polygon shapefile; None for null shapes."""
    if struct.unpack("<i", data[32:36])[0] != 5:
        raise SystemExit("not a polygon shapefile")
    out, pos = [], 100
    while pos < len(data):
        _, clen = struct.unpack(">ii", data[pos:pos + 8])
        body = data[pos + 8: pos + 8 + clen * 2]
        pos += 8 + clen * 2
        if struct.unpack("<i", body[:4])[0] == 0:
            out.append(None)
            continue
        bbox = struct.unpack("<4d", body[4:36])
        nparts, npts = struct.unpack("<ii", body[36:44])
        starts = list(struct.unpack(f"<{nparts}i", body[44:44 + 4 * nparts])) + [npts]
        xy = struct.unpack(f"<{2 * npts}d", body[44 + 4 * nparts: 44 + 4 * nparts + 16 * npts])
        out.append((bbox, [[(xy[2 * k], xy[2 * k + 1]) for k in range(starts[j], starts[j + 1])] for j in range(nparts)]))
    return out


def unit_names(meta_text):
    """PTYPE -> definition from the FGDC metadata's enumerated domain."""
    part = meta_text.split("Attribute_Label: PTYPE", 1)[1].split("Attribute_Label:", 1)[0]
    return dict(re.findall(r"Enumerated_Domain_Value: (\S+)\s+Enumerated_Domain_Value_Definition: ([^\n]+)", part))


def fill_rings(grid, rings, val, x0, y1, cx, cy, cols, rows):
    """Set grid cells whose centre (grid point) lies inside the rings (even-odd) to val."""
    ys = [y for r in rings for _, y in r]
    r0 = max(0, math.ceil((y1 - max(ys)) / cy)); r1 = min(rows - 1, math.floor((y1 - min(ys)) / cy))
    for r in range(r0, r1 + 1):
        yc = y1 - r * cy
        xs = []
        for ring in rings:
            for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
                if (ay > yc) != (by > yc):
                    xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            c0 = max(0, math.ceil((a - x0) / cx)); c1 = min(cols - 1, math.floor((b - x0) / cx))
            for c in range(c0, c1 + 1):
                grid[r][c] = val


def to_utm83(lon, lat, de, dn):
    """NAD27 geographic -> NAD83 / UTM 10N, with the close-up's constant NAD83 -> NAD27 offset (de, dn)."""
    e, n = mg.utm_forward(math.radians(lat), math.radians(lon), mg.CLARKE1866)
    return e - de, n - dn


def build(e00, zpath, meta, out_dir):
    out = Path(out_dir)
    index = json.loads((out / "detail" / "index.json").read_text())
    frame_legend = json.loads((out / "geology_legend.json").read_text())
    known = {u["ptype"]: u["color"] for u in frame_legend["units"]}
    arcs, pat = mg.read_e00(e00)
    with zipfile.ZipFile(zpath) as z:
        polys = read_polygons(z.read("sfq2py.shp"))
        recs = read_dbf(z.read("sfq2py.dbf"))
    names = unit_names(Path(meta).read_text(encoding="latin-1"))
    sim_types = {r["PTYPE"] for r in pat[1:] if r.get("PTYPE")}
    q_types = {RENAME.get(r["PTYPE"], r["PTYPE"]) for r in recs if r and r.get("PTYPE")} - FALLBACK
    colour = dict(mg.palette((sim_types | q_types) - set(known)), **known)
    places = []
    for q in index["locations"]:
        x0, y0, x1, y1 = q["bbox_utm"]
        cols, rows = q["cols"], q["rows"]
        cx, cy = (x1 - x0) / (cols - 1), (y1 - y0) / (rows - 1)
        de, dn = mg.nad83_to_nad27_offset((x0 + x1) / 2, (y0 + y1) / 2)
        poly = mg.rasterize(arcs, x0 - cx / 2 + de, y1 + cy / 2 + dn, cx, cols, rows, cy)
        sim = [[pat[p - 1]["PTYPE"] if 1 < p <= len(pat) else "" for p in row] for row in poly]
        fine = [[None] * cols for _ in range(rows)]
        # the close-up's corners in NAD27 degrees, padded, to skip far polygons before projecting them
        corners = [mg.utm_inverse(e + de, n + dn, mg.CLARKE1866) for e in (x0, x1) for n in (y0, y1)]
        la0, la1 = min(math.degrees(c[0]) for c in corners) - 0.01, max(math.degrees(c[0]) for c in corners) + 0.01
        lo0, lo1 = min(math.degrees(c[1]) for c in corners) - 0.01, max(math.degrees(c[1]) for c in corners) + 0.01
        for shape, rec in zip(polys, recs):
            if not shape or not rec or not rec.get("PTYPE"):
                continue
            (bx0, by0, bx1, by1), rings = shape
            if bx1 < lo0 or bx0 > lo1 or by1 < la0 or by0 > la1:
                continue
            fill_rings(fine, [[to_utm83(lo, la, de, dn) for lo, la in ring] for ring in rings], RENAME.get(rec["PTYPE"], rec["PTYPE"]),
                       x0, y1, cx, cy, cols, rows)
        counts, rgba = {}, bytearray(cols * rows * 4)
        for r in range(rows):
            for c in range(cols):
                f = fine[r][c]
                t, src = (f, "24k") if f and f not in FALLBACK else (sim[r][c], "100k")
                if not t:
                    continue
                key = (t, src)
                counts[key] = counts.get(key, 0) + 1
                h = colour[t]
                rgba[(r * cols + c) * 4:(r * cols + c + 1) * 4] = bytes((int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255))
        if not counts:
            continue
        n24 = sum(k for (t, s), k in counts.items() if s == "24k")
        mg.write_png(out / "detail" / f"{q['id']}.geology.png", rgba, cols, rows)
        units = {}
        for (t, s), k in counts.items():
            u = units.setdefault(t, {"ptype": t, "color": colour[t], "cells": 0, "maps": []})
            u["cells"] += k
            u["maps"] = sorted(set(u["maps"]) | {s})
            nm = names.get(t) or names.get({v: k for k, v in RENAME.items()}.get(t))
            if s == "24k" and nm:
                u["name"] = nm
        places.append({"id": q["id"], "file": f"{q['id']}.geology.png", "cols": cols, "rows": rows,
                       "cell_m": [round(cx, 3), round(cy, 3)], "mapped_fraction": round(sum(counts.values()) / (cols * rows), 3),
                       "fine_fraction": round(n24 / (cols * rows), 3),
                       "units": sorted(units.values(), key=lambda u: -u["cells"])})
    zsha = hashlib.sha256(Path(zpath).read_bytes()).hexdigest()
    doc = {"label": "USGS 1:24,000 young deposits over SIM 2956",
           "source": frame_legend["source"], "rights": frame_legend["rights"], "input": frame_legend["input"],
           "fine": {"label": "USGS OFR 2006-1037, 1:24,000", "source": SOURCE, "rights": "Public domain (USGS)",
                    "input": {"file": Path(zpath).name, "sha256": zsha, "polygons": sum(1 for p in polys if p)},
                    "fallback": sorted(FALLBACK)},
           "grid": "each close-up's own grid (detail/index.json), NAD83 / UTM 10N, row 0 = north, grid points sampled",
           "limits": "Young deposits (Quaternary units) come from the 1:24,000 map where it reaches (north to 38.625 N); "
                     "older rock, and everything beyond that map, from SIM 2956 at 1:100,000 (a line roughly 50 m wide on "
                     "the ground). Each unit lists the map(s) it came from. Transparent cells are outside both maps.",
           "closeups": places}
    (out / "detail" / "geology.json").write_text(json.dumps(doc, indent=1) + "\n")
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("e00", help="SIM 2956 eswn-geol.e00")
    ap.add_argument("--zip", required=True, help="of06-1037_4b.shp.zip")
    ap.add_argument("--meta", required=True, help="of06-1037_9.meta.txt")
    ap.add_argument("--out-dir", default=str(ROOT / "prototype" / "assets" / "regions" / "napa_valley"))
    a = ap.parse_args()
    doc = build(a.e00, a.zip, a.meta, a.out_dir)
    for q in doc["closeups"]:
        print(f"  {q['id']}: {round(q['fine_fraction'] * 100)} % at 1:24,000; "
              + ", ".join(u["ptype"] + ("*" if "24k" in u["maps"] else "") for u in q["units"][:6]))


if __name__ == "__main__":
    main()
