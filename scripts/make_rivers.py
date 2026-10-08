#!/usr/bin/env python3
"""Rivers and creeks for a region frame from the USGS National Hydrography Dataset (NHD, high resolution).

Tier 0, standard library only. Input: the NHD "HU8 Shape" packages for the watersheds that cover the frame,
from the USGS National Map staged products on AWS (prd-tnm.s3.amazonaws.com, reachable from the sandbox; the
National Map web services are not). Each package is one watershed; it is downloaded once to data/raw/nhd/
(git-ignored) and its SHA-256 goes into data/manifest.json. SOURCES.md G26: USGS, public domain, credit USGS.

What is kept: stream/river flowlines (FType 460) and the artificial paths that carry them through lakes and
wide channels (558), each with the channel length upstream of it (upstream_km() below), which sets a size class
1 to 6. Unnamed lines with less than MIN_KM upstream are left out, so the map shows the drainage people talk about. Canals, pipelines and
coastlines are dropped. Lines are clipped to the frame, projected to NAD83 / UTM 10N and simplified
(Douglas-Peucker, --tolerance metres).

Output: <assets_dir>/rivers.json
  {"source", "rights", "names": [...], "lines": [[name_index or -1, size class, perennial 0/1, x0, y0, dx1, dy1, ...]]}
  x, y are whole metres east and north (UTM 10N); after the first vertex, the rest are differences.

These are today's channels, mapped from imagery and surveys, many of them straightened, leveed or piped.
They are not a reconstruction of where the rivers ran before farming.

Usage: make_rivers.py --region data/regions/napa_valley.json [--tolerance 12] [--offline]
"""
import argparse
import datetime
import hashlib
import json
import math
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_terrain import utm_from_geographic  # noqa: E402
from net import open_url  # noqa: E402

URL = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Hydrography/NHD/HU8/Shape/NHD_H_{hu8}_HU8_Shape.zip"
CACHE = ROOT / "data" / "raw" / "nhd"
SOURCE = ("U.S. Geological Survey, National Hydrography Dataset (NHD) high resolution, HU8 staged products "
          "(NHDFlowline)")
RIGHTS = "USGS-produced, public domain in the U.S.; credit U.S. Geological Survey (SOURCES.md G26)"
KEEP_FTYPES = {460, 558}             # StreamRiver, ArtificialPath
PERENNIAL = {46006, 55800}           # StreamRiver perennial; ArtificialPath (carries the main stem)
MIN_KM = 3.0                         # unnamed lines need at least this much channel upstream to be kept


def size_class(km):
    """1 (under 10 km of channel upstream) to 6 (over 1,000 km): the line width class on the map."""
    return 1 + sum(km >= t for t in (10, 40, 150, 400, 1000))


def read_dbf(data):
    """Records of a dBASE III table as dicts (character and numeric fields; others as stripped text)."""
    n, hl, rl = struct.unpack("<IHH", data[4:12])
    fields, off = [], 1
    for i in range(32, hl - 1, 32):
        name = data[i:i + 11].split(b"\0")[0].decode("ascii")
        typ, size = chr(data[i + 11]), data[i + 16]
        fields.append((name, typ, off, size))
        off += size
    out = []
    for r in range(n):
        rec = data[hl + r * rl: hl + (r + 1) * rl]
        if rec[:1] == b"*":
            out.append(None)
            continue
        row = {}
        for name, typ, o, size in fields:
            v = rec[o:o + size].decode("latin-1").strip()
            if typ == "N":
                try:
                    v = float(v) if "." in v else int(v)
                except ValueError:
                    v = None
            row[name] = v
        out.append(row)
    return out


def read_polylines(data):
    """Parts of each record of a PolyLine / PolyLineZ / PolyLineM shapefile, as lists of (x, y)."""
    shp_type = struct.unpack("<i", data[32:36])[0]
    if shp_type not in (3, 13, 23):
        raise SystemExit(f"not a polyline shapefile (type {shp_type})")
    out, pos = [], 100
    while pos < len(data):
        _, clen = struct.unpack(">ii", data[pos:pos + 8])
        body = data[pos + 8: pos + 8 + clen * 2]
        pos += 8 + clen * 2
        if struct.unpack("<i", body[:4])[0] == 0:
            out.append([])
            continue
        nparts, npts = struct.unpack("<ii", body[36:44])
        starts = list(struct.unpack(f"<{nparts}i", body[44:44 + 4 * nparts])) + [npts]
        xy = struct.unpack(f"<{2 * npts}d", body[44 + 4 * nparts: 44 + 4 * nparts + 16 * npts])
        out.append([[(xy[2 * k], xy[2 * k + 1]) for k in range(starts[j], starts[j + 1])] for j in range(nparts)])
    return out


def simplify(pts, tol):
    """Douglas-Peucker on a list of (x, y) in metres."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = pts[a], pts[b]
        dx, dy = bx - ax, by - ay
        den = math.hypot(dx, dy) or 1e-9
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            d = abs(dy * (px - ax) - dx * (py - ay)) / den
            if d > best:
                best, bi = d, i
        if best > tol:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def clip_runs(pts, box):
    """Pieces of a line inside the box (vertices outside are dropped; a piece ends where the line leaves)."""
    x0, y0, x1, y1 = box
    runs, cur = [], []
    for x, y in pts:
        if x0 <= x <= x1 and y0 <= y <= y1:
            cur.append((x, y))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) > 1]


def package(hu8, offline=False):
    path = CACHE / f"NHD_H_{hu8}_HU8_Shape.zip"
    if not path.exists():
        if offline:
            raise SystemExit(f"{path} missing (offline)")
        CACHE.mkdir(parents=True, exist_ok=True)
        with open_url(URL.format(hu8=hu8), timeout=300) as r:
            path.write_bytes(r.read())
    return path


def upstream_km(lines, lengths):
    """Total channel length upstream of each line's end, itself included (the "arbolate sum"), from how the
    lines join: a line's end vertex is the start vertex of the line downstream (NHD lines are digitized in
    the flow direction). Where a channel splits (braids, tidal sloughs), its total is shared equally among the
branches, so a braid does not count the same upstream twice.
    Used to size the lines on the map; the package's own value-added table is not used because some packages
    leave it empty. Strahler order was tried and rejected: the braided, 1:24,000 network inflates it."""
    key = lambda p: (round(p[0], 7), round(p[1], 7))
    starts = {}
    for i, pts in enumerate(lines):
        starts.setdefault(key(pts[0]), []).append(i)
    ups, ndown = [[] for _ in lines], [0] * len(lines)
    for i, pts in enumerate(lines):
        for j in starts.get(key(pts[-1]), []):
            if j != i:
                ups[j].append(i)
                ndown[i] += 1
    acc = [None] * len(lines)
    for i in range(len(lines)):
        if acc[i] is not None:
            continue
        stack, on = [i], {i}
        while stack:                                   # iterative post-order; a cycle (rare) is cut where it closes
            j = stack[-1]
            todo = [u for u in ups[j] if acc[u] is None and u not in on]
            if todo:
                stack += todo
                on.update(todo)
                continue
            stack.pop()
            on.discard(j)
            acc[j] = lengths[j] + sum(acc[u] / ndown[u] for u in ups[j] if acc[u] is not None)
    return acc


def flowlines(zpath, box, tol):
    """(name, order, perennial, [(x, y) UTM m]) for the kept flowlines of one package, clipped to box."""
    z = zipfile.ZipFile(zpath)
    names = {n.split("/")[-1].lower(): n for n in z.namelist()}
    attrs = read_dbf(z.read(names["nhdflowline.dbf"]))
    geoms = read_polylines(z.read(names["nhdflowline.shp"]))
    keep = [(a, [p for part in parts for p in part]) for a, parts in zip(attrs, geoms)
            if a and a["ftype"] in KEEP_FTYPES and parts and sum(len(q) for q in parts) > 1]
    acc = upstream_km([pts for _, pts in keep], [a.get("lengthkm") or 0.0 for a, _ in keep])
    for (a, pts), km in zip(keep, acc):
        name = a.get("gnis_name") or ""
        if km < MIN_KM and not name:
            continue
        so = size_class(km)
        utm = [utm_from_geographic(lat, lon) for lon, lat in pts]
        for run in clip_runs(utm, box):
            yield name, so, int(a["fcode"] in PERENNIAL), simplify(run, tol)


def build(region, tol=12.0, offline=False):
    frame = region["bbox_utm"]
    hu8s = region.get("nhd_hu8") or []
    if not hu8s:
        raise SystemExit("region file has no nhd_hu8 list")
    names, lines, pkgs = [], [], []
    for hu8 in hu8s:
        path = package(hu8, offline)
        pkgs.append({"hu8": hu8, "url": URL.format(hu8=hu8), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                     "bytes": path.stat().st_size})
        for name, so, per, pts in flowlines(path, frame, tol):
            ni = -1
            if name:
                if name not in names:
                    names.append(name)
                ni = names.index(name)
            row = [ni, so, per, round(pts[0][0]), round(pts[0][1])]
            px, py = row[3], row[4]
            for x, y in pts[1:]:
                qx, qy = round(x), round(y)
                row += [qx - px, qy - py]
                px, py = qx, qy
            lines.append(row)
    lines.sort(key=lambda r: (r[1], r[0]))            # draw small streams first, big rivers on top
    return {"source": SOURCE, "rights": RIGHTS, "region": region["id"], "bbox_utm": frame,
            "crs": "NAD83 / UTM 10N, whole metres; first vertex absolute, then differences",
            "kept": f"FType 460 StreamRiver and 558 ArtificialPath with a GNIS name or at least {MIN_KM} km of channel upstream",
            "size_class": "1 to 6 by channel km upstream: <10, 10-40, 40-150, 150-400, 400-1000, >1000",
            "simplify_m": tol, "packages": pkgs, "names": names,
            "fields": ["name_index", "size_class", "perennial", "x0", "y0", "dx1", "dy1", "..."],
            "note": "Today's mapped channels (many straightened or piped), not the pre-settlement river.",
            "lines": lines}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--tolerance", type=float, default=12.0, help="simplification tolerance (m)")
    ap.add_argument("--offline", action="store_true", help="use cached packages only")
    a = ap.parse_args()
    region = json.loads((ROOT / a.region).read_text())
    doc = build(region, a.tolerance, a.offline)
    out = ROOT / region["assets_dir"] / "rivers.json"
    text = json.dumps(doc, separators=(",", ":"))
    out.write_text(text + "\n")
    man_path = ROOT / "data" / "manifest.json"
    man = json.loads(man_path.read_text()) if man_path.exists() else {}
    entries = man.setdefault("datasets", [])
    mid = f"{region['id']}-nhd-rivers"
    entries[:] = [e for e in entries if e.get("id") != mid]
    entries.append({"id": mid, "source": SOURCE, "packages": doc["packages"], "fetched": datetime.date.today().isoformat(),
                    "rights": RIGHTS, "derived": [{"file": str(out.relative_to(ROOT)),
                                                   "sha256": hashlib.sha256((text + "\n").encode()).hexdigest()}]})
    man_path.write_text(json.dumps(man, indent=2) + "\n")
    top = {}
    for r in doc["lines"]:
        if r[0] >= 0:
            top[doc["names"][r[0]]] = max(top.get(doc["names"][r[0]], 0), r[1])
    big = sorted(top.items(), key=lambda kv: -kv[1])[:8]
    print(f"{len(doc['lines'])} lines, {len(doc['names'])} names, {len(text) / 1e6:.2f} MB; largest: "
          + ", ".join(f"{n} ({c})" for n, c in big))


if __name__ == "__main__":
    main()
