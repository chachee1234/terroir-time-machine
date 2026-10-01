#!/usr/bin/env python3
"""Napa Valley before farming: SFEI's Historical Ecology GIS data (2011) turned into viewer layers.

Tier 0, standard library only. Input: the owner-downloaded Napa_historical_ecology_GIS_data_SFEI_2011.zip
(www.sfei.org blocks scripted downloads), which holds an Esri file geodatabase in California State Plane II
feet. A small file-geodatabase reader below (after the OpenFileGDB format notes by Even Rouault) reads the
three feature classes:
  Historical_Channels        lines: Mainstem, Historical Channel, Floodplain Slough, Paleochannel,
                             Spring Channel, Tidal Channel
  Historical_Distributaries  lines where channels spread out and ended on the valley floor
  Historical_Habitats        polygons: Valley Oak Savanna, Wet Meadow, Valley Freshwater Marsh, ...
Each feature keeps SFEI's certainty codes (interpretation, shape, location: H/M/L; location H < 50 m,
M < 150 m, L < 500 m maximum displacement).

Output: <assets_dir>/historical_ecology.json
  {"source", "rights", "classes": {"channels": [...], "habitats": [...]},
   "channels": [[class index, interp, loc, x0, y0, dx1, dy1, ...]],      (distributaries use class names too)
   "habitats": [[class index, interp, loc, [ring: x0, y0, dx1, dy1, ...], ...]]}
  x, y whole metres east and north, NAD83 / UTM 10N, like rivers.json. Habitats are simplified at --tolerance.

Rights: San Francisco Estuary Institute 2011, distributed under the GNU General Public License v3 or later
(SFEI data page). Credit SFEI. SOURCES.md G31.

Usage: make_historical_ecology.py --zip <path to the SFEI zip> --region data/regions/napa_valley.json
"""
import argparse
import datetime
import hashlib
import io
import json
import math
import re
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_terrain import utm_from_geographic  # noqa: E402
from make_rivers import simplify  # noqa: E402

LAYERS = {"Historical_Channels": "channels", "Historical_Distributaries": "distributaries",
          "Historical_Habitats": "habitats"}
SOURCE = ("San Francisco Estuary Institute (SFEI) 2011, Napa Valley Historical Ecology Atlas GIS data "
          "(Historical_Channels, Historical_Distributaries, Historical_Habitats), "
          "https://www.sfei.org/data/napa-historical-ecology-atlas-gis-data")
RIGHTS = "SFEI 2011, GNU General Public License v3 or later; credit San Francisco Estuary Institute."
CERT = {"H": 2, "M": 1, "L": 0}


def varuint(b, p):
    r = s = 0
    while True:
        c = b[p]
        p += 1
        r |= (c & 0x7F) << s
        s += 7
        if not c & 0x80:
            return r, p


def varint(b, p):
    c = b[p]
    p += 1
    r, neg, s = c & 0x3F, c & 0x40, 6
    while c & 0x80:
        c = b[p]
        p += 1
        r |= (c & 0x7F) << s
        s += 7
    return (-r if neg else r), p


class Table:
    """One feature class or table of an Esri file geodatabase (10.x format): fields, rows, shapes."""

    def __init__(self, table, tablx):
        self.b, b = table, table
        fo = struct.unpack("<q", b[32:40])[0]
        _, _, lflags, nf = struct.unpack("<iiIh", b[fo:fo + 14])
        self.geom_type = lflags & 0xFF
        p, self.fields = fo + 14, []
        self.has_z = self.has_m = False
        for _ in range(nf):
            n = b[p]
            name = b[p + 1:p + 1 + 2 * n].decode("utf-16le")
            p += 1 + 2 * n
            p += 1 + 2 * b[p]
            ty = b[p]
            p += 1
            nullable = False
            if ty == 4:
                fl = b[p + 4]
                p += 5
                nullable = bool(fl & 1)
                if fl & 4:
                    ln, p = varuint(b, p)
                    p += ln
            elif ty == 6:
                p += 2
            elif ty == 7:
                fl = b[p + 1]
                p += 2
                nullable = bool(fl & 1)
                wl = struct.unpack("<H", b[p:p + 2])[0]
                self.wkt = b[p + 2:p + 2 + wl].decode("utf-16le")
                p += 2 + wl
                flags = b[p]
                p += 1
                self.has_m, self.has_z = bool(flags & 2), bool(flags & 4)
                self.xo, self.yo, self.scale = struct.unpack("<3d", b[p:p + 24])
                p += 24
                p += 16 * self.has_m + 16 * self.has_z          # origin + scale for m, z
                p += 8 + 8 * self.has_m + 8 * self.has_z         # tolerances
                p += 32 + 1                                      # extent, then one unknown byte
                ng = struct.unpack("<i", b[p:p + 4])[0]
                p += 4 + 8 * ng
            elif ty in (8, 12):
                fl = b[p + 1]
                p += 2
                nullable = bool(fl & 1)
            elif ty in (10, 11):
                fl = b[p + 1]
                p += 2
                nullable = bool(fl & 1)
            else:
                fl = b[p + 1]
                p += 2
                nullable = bool(fl & 1)
                ln = b[p]
                p += 1 + ln
            self.fields.append((name, ty, nullable))
        x = tablx
        n1024, nrows, osz = struct.unpack("<iii", x[4:16])
        self.offsets = [int.from_bytes(x[16 + i * osz:16 + (i + 1) * osz], "little") for i in range(nrows)]

    def rows(self):
        b = self.b
        nnull = sum(1 for f in self.fields if f[2])
        for oid, off in enumerate(self.offsets, start=1):
            if not off:
                continue
            p = off + 4
            flags = b[p:p + (nnull + 7) // 8]
            p += len(flags)
            row, k = {"_id": oid}, 0
            for name, ty, nullable in self.fields:
                if ty == 6:
                    continue
                if nullable:
                    isnull = flags[k // 8] >> (k % 8) & 1
                    k += 1
                    if isnull:
                        row[name] = None
                        continue
                if ty == 0:
                    row[name] = struct.unpack("<h", b[p:p + 2])[0]
                    p += 2
                elif ty in (1, 2):
                    row[name] = struct.unpack("<i" if ty == 1 else "<f", b[p:p + 4])[0]
                    p += 4
                elif ty in (3, 5):
                    row[name] = struct.unpack("<d", b[p:p + 8])[0]
                    p += 8
                elif ty in (4, 12):
                    ln, p = varuint(b, p)
                    row[name] = b[p:p + ln].decode("utf-8", "replace")
                    p += ln
                elif ty in (7, 8):
                    ln, p = varuint(b, p)
                    row[name] = self.shape(b[p:p + ln]) if ty == 7 else b[p:p + ln]
                    p += ln
                elif ty in (10, 11):
                    p += 16
                else:
                    raise SystemExit(f"field type {ty} not handled")
            yield row

    def shape(self, g):
        """Parts of a polyline or polygon as lists of (x, y) in the layer's units."""
        st, p = varuint(g, 0)
        base = st & 0xFF
        if base not in (3, 5, 10, 13, 15, 19, 23, 25, 50, 51):
            raise SystemExit(f"shape type {st} not handled")
        npts, p = varuint(g, p)
        nparts, p = varuint(g, p)
        if st & 0x20000000:
            _, p = varuint(g, p)                             # curve count; curves are dropped
        for _ in range(4):
            _, p = varuint(g, p)                             # envelope
        sizes = []
        for _ in range(nparts - 1):
            n, p = varuint(g, p)
            sizes.append(n)
        sizes.append(npts - sum(sizes))
        x = y = 0
        parts = []
        for n in sizes:
            part = []
            for _ in range(n):
                dx, p = varint(g, p)
                dy, p = varint(g, p)
                x, y = x + dx, y + dy
                part.append((x / self.scale + self.xo, y / self.scale + self.yo))
            parts.append(part)
        return parts


def read_gdb(zpath):
    z = zipfile.ZipFile(zpath)
    names = z.namelist()
    gdb = next(n.split("/")[0] for n in names if ".gdb/" in n)
    rd = lambda i, ext: z.read(f"{gdb}/a{i:08x}.{ext}")
    cat = Table(rd(1, "gdbtable"), rd(1, "gdbtablx"))
    out = {}
    for row in cat.rows():
        if row.get("Name") in LAYERS:
            out[LAYERS[row["Name"]]] = Table(rd(row["_id"], "gdbtable"), rd(row["_id"], "gdbtablx"))
    return out


def lcc_inverse(wkt):
    """Lambert conformal conic (2SP) inverse from an Esri WKT, GRS80; returns f(x, y) -> (lat, lon)."""
    par = {k: float(v) for k, v in re.findall(r'PARAMETER\["(\w+)",(-?[\d.]+)\]', wkt)}
    unit = float(re.findall(r'UNIT\["[^"]+",([\d.]+)\]\]$', wkt.strip())[0])
    a, f = 6378137.0, 1 / 298.257222101
    e = math.sqrt(2 * f - f * f)
    p1, p2, p0 = (math.radians(par[k]) for k in ("Standard_Parallel_1", "Standard_Parallel_2", "Latitude_Of_Origin"))
    l0 = math.radians(par["Central_Meridian"])
    m = lambda p: math.cos(p) / math.sqrt(1 - (e * math.sin(p)) ** 2)
    t = lambda p: math.tan(math.pi / 4 - p / 2) / ((1 - e * math.sin(p)) / (1 + e * math.sin(p))) ** (e / 2)
    n = (math.log(m(p1)) - math.log(m(p2))) / (math.log(t(p1)) - math.log(t(p2)))
    F = m(p1) / (n * t(p1) ** n)
    r0 = a * F * t(p0) ** n
    fe, fn = par["False_Easting"] * unit, par["False_Northing"] * unit

    def inv(x, y):
        x, y = x * unit - fe, r0 - (y * unit - fn)
        r = math.copysign(math.hypot(x, y), n)
        tt = (r / (a * F)) ** (1 / n)
        th = math.atan2(x, y)
        lat = math.pi / 2 - 2 * math.atan(tt)
        for _ in range(8):
            lat = math.pi / 2 - 2 * math.atan(tt * ((1 - e * math.sin(lat)) / (1 + e * math.sin(lat))) ** (e / 2))
        return math.degrees(lat), math.degrees(th / n + l0)
    return inv


def simplify_ring(pts, tol):
    """Douglas-Peucker on a closed ring, in two halves so the shared first/last vertex doesn't collapse it."""
    if len(pts) < 8:
        return pts
    h = len(pts) // 2
    return simplify(pts[:h + 1], tol)[:-1] + simplify(pts[h:], tol)


def encode(pts):
    out = [round(pts[0][0]), round(pts[0][1])]
    px, py = out
    for x, y in pts[1:]:
        x, y = round(x), round(y)
        if (x, y) != (px, py):
            out += [x - px, y - py]
            px, py = x, y
    return out


def build(zpath, region_path, tolerance=8.0):
    region = json.loads(Path(region_path).read_text())
    x0, y0, x1, y1 = region["bbox_utm"]
    tabs = read_gdb(zpath)
    inv = lcc_inverse(tabs["channels"].wkt)
    utm = lambda pt: utm_from_geographic(*inv(*pt))
    inside = lambda pts: any(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts)
    classes = {"channels": [], "habitats": []}
    idx = lambda kind, name: classes[kind].index(name) if name in classes[kind] else (classes[kind].append(name) or len(classes[kind]) - 1)
    cert = lambda r, k: CERT.get((r.get(k) or "").strip()[:1].upper(), -1)
    out = {"channels": [], "habitats": []}
    for kind in ("channels", "distributaries"):
        for r in tabs[kind].rows():
            for part in next(v for v in r.values() if isinstance(v, list)):
                pts = [utm(p) for p in part]
                if len(pts) < 2 or not inside(pts):
                    continue
                pts = simplify(pts, tolerance / 2)
                name = (r.get("Habitat_Type") or "Unknown").strip()
                if kind == "distributaries" and not name.startswith("Distributary"):
                    name = "Distributary: " + name
                out["channels"].append([idx("channels", name), cert(r, "InterpCert"), cert(r, "Loc_Cert")] + encode(pts))
    for r in tabs["habitats"].rows():
        geom = next(v for v in r.values() if isinstance(v, list))
        rings = [simplify_ring([utm(p) for p in ring], tolerance) for ring in geom]
        rings = [rg for rg in rings if len(rg) >= 3]
        if not rings or not inside([p for rg in rings for p in rg]):
            continue
        out["habitats"].append([idx("habitats", (r.get("Habitat_Type") or "Unknown").strip()),
                                cert(r, "InterpCert"), cert(r, "Loc_Cert")] + [encode(rg) for rg in rings])
    doc = {"source": SOURCE, "rights": RIGHTS, "built": datetime.date.today().isoformat(),
           "input_sha256": hashlib.sha256(Path(zpath).read_bytes()).hexdigest(),
           "period": "circa 1769-1850 (before Euro-American modification), per SFEI",
           "certainty": "interp/loc: 2 = high, 1 = medium, 0 = low, -1 = not given. Location high < 50 m, "
                        "medium < 150 m, low < 500 m maximum displacement (SFEI metadata).",
           "classes": classes, **out}
    path = ROOT / region["assets_dir"] / "historical_ecology.json"
    path.write_text(json.dumps(doc, separators=(",", ":")) + "\n")
    return doc, path


def decode(row, start):
    x, y = row[start], row[start + 1]
    pts = [(x, y)]
    for k in range(start + 2, len(row), 2):
        x, y = x + row[k], y + row[k + 1]
        pts.append((x, y))
    return pts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--tolerance", type=float, default=8.0)
    a = ap.parse_args()
    doc, path = build(a.zip, a.region, a.tolerance)
    from collections import Counter
    ch = Counter(doc["classes"]["channels"][r[0]] for r in doc["channels"])
    hb = Counter(doc["classes"]["habitats"][r[0]] for r in doc["habitats"])
    print(f"{path.relative_to(ROOT)}: {len(doc['channels'])} channel lines {dict(ch)}; "
          f"{len(doc['habitats'])} habitat polygons {dict(hb)}")


if __name__ == "__main__":
    main()
