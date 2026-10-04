#!/usr/bin/env python3
"""Mapped vineyard fields in a region frame from California DWR Statewide Crop Mapping (Land IQ for DWR).

Tier 0, standard library only. DWR publishes one statewide shapefile per year (a ZIP of a few hundred MB on
data.cnra.ca.gov). It is downloaded once into data/raw/dwr/ (git-ignored), or given with --zip if it was saved
from a browser. The ZIP is read in place, record by record: only fields whose box touches the frame and whose
main crop is Vineyard are kept, so nothing statewide is extracted or committed.

Unlike the USDA Cropland Data Layer (make_vineyards.py, 30 m satellite cells), these are field outlines that
Land IQ drew and classified (DWR reports ~98 % accuracy at the class level), so block edges, small blocks and
hillside vineyards come through.

Output:
  <assets_dir>/vineyard_fields.json   field count, DWR's own acres, and acres per AVA polygon, per year, with a
                                      side-by-side CDL figure when vineyards.json exists
  <assets_dir>/vineyard_fields.png    latest year's vineyard fields on a 20 m grid over the frame (north up,
                                      transparent elsewhere); the viewer paints today's vines from it

Limits: one season's main crop per field; "Young Perennial" fields (new plantings not yet identifiable as
vines) are not counted; fields are classified from imagery, not from grower reports; WGS84/NAD83 treated as
the same (about 1 m here). Acres per AVA count 20 m cells, so a few blocks on an AVA edge are split.

Rights: California DWR, "No restrictions on public use" (data.ca.gov listing). Credit: California Department
of Water Resources and Land IQ. SOURCES.md G33.

Usage: make_dwr_vineyards.py --region data/regions/napa_valley.json [--years 2023] [--zip FILE] [--offline]
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
import urllib.request
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_terrain import utm_from_geographic  # noqa: E402
from fetch_tiles import geographic_from_utm  # noqa: E402

CACHE = ROOT / "data" / "raw" / "dwr"
CELL = 20.0                                  # drape grid; 76 km frame -> 3810 x 3825, under the 4096 texture limit
ACRES_PER_M2 = 1 / 4046.8564224
COLOR = (0x5e, 0x8c, 0x31)
_B = "https://data.cnra.ca.gov/dataset/6c3d65e3-35bb-49e1-a51e-49d5a2cf09a9/resource/"
URLS = {                                      # shapefile ZIPs as listed on data.ca.gov "Statewide Crop Mapping"
    2014: _B + "3bba74e2-a992-48db-a9ed-19e6fabb8052/download/i15_crop_mapping_2014_shp.zip",
    2016: _B + "3b57898b-f013-487a-b472-17f54311edb5/download/i15_crop_mapping_2016_shp.zip",
    2018: _B + "2dde4303-5c83-4980-a1af-4f321abefe95/download/i15_crop_mapping_2018_shp.zip",
    2019: _B + "1da7b37a-dd97-4b69-a86a-fe824a252eaf/download/i15_crop_mapping_2019.zip",
    2020: _B + "11dde2fe-dc07-4b10-b54e-ede2b4ce5fe6/download/i15_crop_mapping_2020.zip",
    2021: _B + "eebd40ab-35a3-4e62-a625-0275b2849531/download/i15_crop_mapping_2021_shp.zip",
    2022: _B + "b92e0daf-6e2e-4b5c-a112-09474138d1cd/download/i15_crop_mapping_2022_shp.zip",
    2023: _B + "25d0f174-4bec-4987-a402-602cd1372786/download/i15_crop_mapping_final_2023.zip",
    2024: _B + "1a1c259c-4279-4868-a25f-b1f71665ca25/download/i15_crop_mapping_2024_provisional.zip",
}
PROVISIONAL = {2024}
SOURCE = ("California DWR Statewide Crop Mapping (Land IQ for DWR), shapefile from data.cnra.ca.gov "
          "(https://data.cnra.ca.gov/dataset/statewide-crop-mapping)")
RIGHTS = ("California Department of Water Resources; data.ca.gov lists 'No restrictions on public use'. "
          "Credit: California Department of Water Resources and Land IQ.")
LIMITS = ("Field outlines classified from imagery by Land IQ for DWR, one main crop per field and year. Young "
          "Perennial fields (new plantings) are not counted as vineyard. Acres per AVA count 20 m cells; AVAs overlap "
          "(sub-AVAs sit inside Napa Valley), so AVA acres do not add up.")
# Main-crop field, first one present wins. Code fields hold DWR class codes (V = Vineyard); name fields hold text.
CODE_FIELDS = ["MAIN_CROP", "CROPTYP2", "CLASS2"]
NAME_FIELDS = ["DWR_STANDA", "CROP2016", "CROP2014", "CROP_TYPE", "CROPTYPE"]


# ---------------------------------------------------------------- projections (from the shapefile's .prj)
def _params(prj):
    p = {k.lower(): float(v) for k, v in re.findall(r'PARAMETER\["([^"]+)",\s*([-+0-9.eE]+)\]', prj)}
    s = re.search(r'SPHEROID\["[^"]*",\s*([0-9.]+),\s*([0-9.]+)', prj)
    a, invf = (float(s.group(1)), float(s.group(2))) if s else (6378137.0, 298.257222101)
    return p, a, invf


class Albers:
    """Ellipsoidal Albers equal-area conic, forward and inverse (Snyder 1987, eqs 14-1..14-21)."""

    def __init__(self, lat1, lat2, lat0, lon0, fe=0.0, fn=0.0, a=6378137.0, invf=298.257222101):
        f = 1 / invf
        self.a, self.e2 = a, 2 * f - f * f
        self.e = math.sqrt(self.e2)
        self.lon0, self.fe, self.fn = math.radians(lon0), fe, fn
        p1, p2, p0 = map(math.radians, (lat1, lat2, lat0))
        m1, m2 = self._m(p1), self._m(p2)
        q1, q2 = self._q(p1), self._q(p2)
        self.n = (m1 * m1 - m2 * m2) / (q2 - q1) if lat1 != lat2 else math.sin(p1)
        self.C = m1 * m1 + self.n * q1
        self.rho0 = self._rho(p0)

    def _m(self, p):
        return math.cos(p) / math.sqrt(1 - self.e2 * math.sin(p) ** 2)

    def _q(self, p):
        s, e = math.sin(p), self.e
        return (1 - self.e2) * (s / (1 - self.e2 * s * s) - math.log((1 - e * s) / (1 + e * s)) / (2 * e))

    def _rho(self, p):
        return self.a * math.sqrt(max(0.0, self.C - self.n * self._q(p))) / self.n

    def forward(self, lat, lon):
        th = self.n * (math.radians(lon) - self.lon0)
        r = self._rho(math.radians(lat))
        return self.fe + r * math.sin(th), self.fn + self.rho0 - r * math.cos(th)

    def inverse(self, x, y):
        x, y = x - self.fe, self.rho0 - (y - self.fn)
        rho = math.copysign(math.hypot(x, y), self.n)
        th = math.atan2(x, y) if self.n > 0 else math.atan2(-x, -y)
        q = (self.C - (rho * self.n / self.a) ** 2) / self.n
        phi, e, e2 = math.asin(max(-1.0, min(1.0, q / 2))), self.e, self.e2
        for _ in range(15):
            s = math.sin(phi)
            d = ((1 - e2 * s * s) ** 2 / (2 * math.cos(phi))
                 * (q / (1 - e2) - s / (1 - e2 * s * s) + math.log((1 - e * s) / (1 + e * s)) / (2 * e)))
            phi += d
            if abs(d) < 1e-12:
                break
        return math.degrees(phi), math.degrees(self.lon0 + th / self.n)


class WebMercator:
    R = 6378137.0

    def forward(self, lat, lon):
        return self.R * math.radians(lon), self.R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

    def inverse(self, x, y):
        return math.degrees(2 * math.atan(math.exp(y / self.R)) - math.pi / 2), math.degrees(x / self.R)


class Geographic:
    def forward(self, lat, lon):
        return lon, lat

    def inverse(self, x, y):
        return y, x


class Utm10:
    def forward(self, lat, lon):
        return utm_from_geographic(lat, lon)

    def inverse(self, x, y):
        return geographic_from_utm(x, y)


def crs_from_prj(prj):
    """The shapefile's coordinate system from its .prj (ESRI WKT). Only the systems DWR has used are accepted."""
    if not prj.strip().upper().startswith("PROJCS"):
        if "GEOGCS" in prj.upper():
            return "geographic", Geographic()
        raise SystemExit(f"unreadable .prj: {prj[:120]!r}")
    p, a, invf = _params(prj)
    up = prj.upper()
    if "UNIT[\"METER\"" not in up.replace(" ", "") and "UNIT[\"METRE\"" not in up.replace(" ", ""):
        raise SystemExit(f"projected .prj is not in metres: {prj[:160]!r}")
    if "MERCATOR_AUXILIARY_SPHERE" in up or "WEB_MERCATOR" in up or "POPULAR_VISUALISATION" in up:
        return "web-mercator (EPSG:3857)", WebMercator()
    if "ALBERS" in up:
        lat0 = p.get("latitude_of_origin", p.get("latitude_of_center", 0.0))
        lon0 = p.get("central_meridian", p.get("longitude_of_center"))
        al = Albers(p["standard_parallel_1"], p["standard_parallel_2"], lat0, lon0,
                    p.get("false_easting", 0.0), p.get("false_northing", 0.0), a, invf)
        return f"albers ({p['standard_parallel_1']}, {p['standard_parallel_2']}; {lat0}, {lon0})", al
    if "TRANSVERSE_MERCATOR" in up and p.get("central_meridian") == -123.0 and abs(p.get("scale_factor", 0) - 0.9996) < 1e-9:
        return "utm 10N", Utm10()
    raise SystemExit(f"unsupported projection in .prj: {prj[:200]!r}")


# ---------------------------------------------------------------- shapefile + dBASE, streamed from the ZIP
def _member(zf, ext):
    names = [i for i in zf.infolist() if i.filename.lower().endswith(ext) and "__macosx" not in i.filename.lower()]
    if not names:
        raise SystemExit(f"no {ext} in the ZIP")
    return max(names, key=lambda i: i.file_size)


def read_dbf_header(f):
    head = f.read(32)
    nrec, hlen, rlen = struct.unpack("<IHH", head[4:12])
    rest = f.read(hlen - 32)
    fields, off = [], 1                       # byte 0 of each record is the deletion flag
    for i in range(0, len(rest) - 1, 32):
        d = rest[i:i + 32]
        if d[0] == 0x0D:
            break
        name = d[:11].split(b"\0")[0].decode("latin-1").strip()
        fields.append((name, chr(d[11]), off, d[16]))
        off += d[16]
    return nrec, rlen, fields


def records(zf):
    """Yield (shape bbox, rings or None, attribute getter) for every record, shapefile and table in step."""
    shp, dbf = zf.open(_member(zf, ".shp")), zf.open(_member(zf, ".dbf"))
    shp.read(100)
    nrec, rlen, fields = read_dbf_header(dbf)
    cols = {name.upper(): (off, ln) for name, _t, off, ln in fields}
    yield {"fields": [f[0] for f in fields], "count": nrec}
    for _ in range(nrec):
        h = shp.read(8)
        if len(h) < 8:
            break
        clen = struct.unpack(">ii", h)[1] * 2
        body = shp.read(clen)
        row = dbf.read(rlen)
        if row[:1] == b"*":
            continue
        st = struct.unpack("<i", body[:4])[0]
        if st not in (5, 15, 25):
            continue
        bbox = struct.unpack("<4d", body[4:36])

        def attr(name, row=row):
            c = cols.get(name)
            return row[c[0]:c[0] + c[1]].decode("latin-1").strip() if c else None

        def rings(body=body):
            nparts, npts = struct.unpack("<ii", body[36:44])
            parts = list(struct.unpack(f"<{nparts}i", body[44:44 + 4 * nparts])) + [npts]
            base = 44 + 4 * nparts
            xy = struct.unpack(f"<{2 * npts}d", body[base:base + 16 * npts])
            return [[(xy[2 * k], xy[2 * k + 1]) for k in range(parts[j], parts[j + 1])] for j in range(nparts)]
        yield bbox, rings, attr


def classifier(fields):
    """(field name, test) for the main crop. Raises with the field list if no known field is present."""
    up = {f.upper() for f in fields}
    for f in CODE_FIELDS:
        if f in up:
            return f, lambda v: v.upper().startswith("V")
    for f in NAME_FIELDS:
        if f in up:
            return f, lambda v: "VINEYARD" in v.upper() or "GRAPE" in v.upper()
    raise SystemExit("no main-crop field found; fields are: " + ", ".join(fields)
                     + ". Add the right one to CODE_FIELDS or NAME_FIELDS in make_dwr_vineyards.py.")


# ---------------------------------------------------------------- scanline fill on the frame grid
def spans(rings_utm, x0, y1, cell, cols, rows):
    """{row: [(c0, c1), ...]} of cells whose centres fall inside the rings (even-odd, so holes stay empty)."""
    rx = {}
    for ring in rings_utm:
        for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
            if ay == by:
                continue
            lo, hi = min(ay, by), max(ay, by)
            r0 = max(0, math.ceil((y1 - hi) / cell - 0.5))
            r1 = min(rows - 1, math.floor((y1 - lo) / cell - 0.5))
            for r in range(r0, r1 + 1):
                yc = y1 - (r + 0.5) * cell
                if lo <= yc < hi:
                    rx.setdefault(r, []).append(ax + (yc - ay) * (bx - ax) / (by - ay))
    out = {}
    for r, xs in rx.items():
        xs.sort()
        s = []
        for a, b in zip(xs[::2], xs[1::2]):
            c0 = max(0, math.ceil((a - x0) / cell - 0.5))
            c1 = min(cols - 1, math.ceil((b - x0) / cell - 0.5) - 1)
            if c1 >= c0:
                s.append((c0, c1))
        if s:
            out[r] = s
    return out


def write_png(path, w, h, mask):
    """Paletted PNG: index 1 = vineyard field, index 0 transparent."""
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    raw = bytearray()
    for r in range(h):
        raw.append(0)
        raw += mask[r * w:(r + 1) * w]
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0))
                     + chunk(b"PLTE", bytes((0, 0, 0) + COLOR)) + chunk(b"tRNS", bytes((0, 255)))
                     + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- build
def fetch(year, given=None, offline=False):
    if given:
        return Path(given)
    if year not in URLS:
        raise SystemExit(f"no DWR crop map listed for {year}; years: {sorted(URLS)}")
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"i15_crop_mapping_{year}.zip"
    if not path.exists():
        if offline:
            raise SystemExit(f"{path} missing and --offline set")
        print(f"downloading {URLS[year]} (statewide, a few hundred MB; once)", file=sys.stderr)
        tmp = path.with_suffix(".part")
        with urllib.request.urlopen(URLS[year], timeout=600) as r, open(tmp, "wb") as out:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                out.write(b)
        tmp.rename(path)
    return path


def frame_box(region, crs, pad_m=300.0):
    """The frame's envelope in the shapefile's own coordinates, padded, for the cheap per-record box test."""
    x0, y0, x1, y1 = region["bbox_utm"]
    pts = [crs.forward(*geographic_from_utm(e, n))
           for e in (x0 - pad_m, (x0 + x1) / 2, x1 + pad_m) for n in (y0 - pad_m, (y0 + y1) / 2, y1 + pad_m)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def read_fields(zip_path, region, crs=None):
    """Vineyard fields touching the frame: (rings in frame UTM, DWR acres, centre in frame?) plus an audit dict."""
    with zipfile.ZipFile(zip_path) as zf:
        prj = zf.read(_member(zf, ".prj")).decode("latin-1")
        name, proj = crs_from_prj(prj) if crs is None else crs
        bx0, by0, bx1, by1 = frame_box(region, proj)
        it = records(zf)
        meta = next(it)
        field, is_vine = classifier(meta["fields"])
        acres_f = next((f for f in meta["fields"] if f.upper() == "ACRES"), None)
        fx0, fy0, fx1, fy1 = region["bbox_utm"]
        kept, values, seen = [], {}, {}
        for bbox, rings, attr in it:
            if bbox[2] < bx0 or bbox[0] > bx1 or bbox[3] < by0 or bbox[1] > by1:
                continue
            v = attr(field) or ""
            seen[v] = seen.get(v, 0) + 1
            if not is_vine(v):
                continue
            utm = [[utm_from_geographic(*proj.inverse(x, y)) for x, y in ring] for ring in rings()]
            pts = [p for ring in utm for p in ring]
            cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
            cy = (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2
            if cx < fx0 - 2000 or cx > fx1 + 2000 or cy < fy0 - 2000 or cy > fy1 + 2000:
                continue
            a = attr(acres_f.upper()) if acres_f else None
            kept.append((utm, float(a) if a else None, fx0 <= cx <= fx1 and fy0 <= cy <= fy1))
            values[v] = values.get(v, 0) + 1
    if not kept:
        top = ", ".join(f"{k or '(blank)'} {n}" for k, n in sorted(seen.items(), key=lambda kv: -kv[1])[:12])
        raise SystemExit(f"no vineyard fields in the frame by {field}; values seen there: {top}")
    return kept, {"crs": name, "field": field, "matched_values": values, "fields_in_frame": sum(k[2] for k in kept),
                  "dwr_acres_in_frame": round(sum(k[1] or 0 for k in kept if k[2]))}


def ava_spans(region, x0, y1, cols, rows):
    out = {}
    for f in json.loads((ROOT / region["boundary"]).read_text())["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        rings = [[utm_from_geographic(lat, lon) for lon, lat in ring[:-1]] for poly in polys for ring in poly]
        out[f["properties"]["name"].strip()] = spans(rings, x0, y1, CELL, cols, rows)
    return out


def cdl_compare(assets, year):
    p = assets / "vineyards.json"
    if not p.exists():
        return None
    v = json.loads(p.read_text())
    ys = sorted(v.get("years", {}), key=lambda y: abs(int(y) - year))
    if not ys:
        return None
    y = v["years"][ys[0]]
    return {"cdl_year": int(ys[0]), "frame_acres": y["frame_acres"], "napa_valley_ava_acres": y["ava_acres"].get("Napa Valley"),
            "note": "USDA CDL 30 m satellite cells (vineyards.json, G30), nearest year; a different method, for comparison"}


def build(region_path, years, zip_path=None, offline=False, out_dir=None, update_index=True):
    region = json.loads(Path(region_path).read_text())
    assets = Path(out_dir) if out_dir else ROOT / region["assets_dir"]
    x0, y0, x1, y1 = region["bbox_utm"]
    cols, rows = int(round((x1 - x0) / CELL)), int(round((y1 - y0) / CELL))
    avas = ava_spans(region, x0, y1, cols, rows)
    cell_ac = CELL * CELL * ACRES_PER_M2
    out = {"source": SOURCE, "rights": RIGHTS, "built": datetime.date.today().isoformat(), "class": "DWR class V (Vineyard)",
           "cell_m": CELL, "frame_cells": [cols, rows], "limits": LIMITS, "years": {}, "files": {}}
    latest = None
    for year in sorted(years):
        path = fetch(year, zip_path, offline)
        fields, audit = read_fields(path, region)
        mask = bytearray(cols * rows)
        for rings, _a, _in in fields:
            for r, ss in spans(rings, x0, y1, CELL, cols, rows).items():
                base = r * cols
                for c0, c1 in ss:
                    mask[base + c0:base + c1 + 1] = b"\x01" * (c1 - c0 + 1)
        by_ava = {name: round(sum(mask[r * cols + c0:r * cols + c1 + 1].count(1) for r, ss in sp.items() for c0, c1 in ss) * cell_ac)
                  for name, sp in avas.items()}
        y = {"status": "provisional" if year in PROVISIONAL else "final", **audit,
             "frame_acres": round(mask.count(1) * cell_ac),
             "ava_acres": dict(sorted(by_ava.items(), key=lambda kv: -kv[1]))}
        cmp_ = cdl_compare(assets, year)
        if cmp_:
            y["cdl_compare"] = cmp_
        out["years"][str(year)] = y
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
        out["files"][str(year)] = {"file": path.name, "url": URLS.get(year), "bytes": path.stat().st_size,
                                   "sha256": h.hexdigest()}
        latest = (year, mask)
        print(f"{year}: {audit['fields_in_frame']} vineyard fields, {y['frame_acres']} acres in the frame "
              f"(DWR's own acres {audit['dwr_acres_in_frame']}); field {audit['field']}, {audit['crs']}", file=sys.stderr)
    year, mask = latest
    assets.mkdir(parents=True, exist_ok=True)
    write_png(assets / "vineyard_fields.png", cols, rows, mask)
    out["drape"] = {"file": "vineyard_fields.png", "year": year, "bbox_utm": region["bbox_utm"], "epsg": region["epsg"]}
    (assets / "vineyard_fields.json").write_text(json.dumps(out, indent=1) + "\n")
    if update_index:
        add_layer(region["id"])
        record_manifest(region, out, assets)
    return out


def add_layer(rid, layer="vineyard_fields"):
    """List the drape in assets/regions/index.json so the viewer asks for it."""
    p = ROOT / "prototype" / "assets" / "regions" / "index.json"
    if not p.exists():
        return
    idx = json.loads(p.read_text())
    for r in idx.get("regions", []):
        if r["id"] == rid and layer not in r.setdefault("layers", []):
            r["layers"].append(layer)
            p.write_text(json.dumps(idx, indent=1) + "\n")


def record_manifest(region, out, assets):
    p = ROOT / "data" / "manifest.json"
    if not p.exists():
        return
    m = json.loads(p.read_text())
    did = f"{region['id']}-dwr-crop-mapping"
    entry = {"id": did, "source": "California DWR Statewide Crop Mapping shapefile ZIP (data.cnra.ca.gov), read in place; "
                                  "vineyard fields in the frame only",
             "packages": [{"year": int(y), **f} for y, f in out["files"].items()],
             "fetched": out["built"], "rights": "California DWR, no restrictions on public use; credit DWR and Land IQ (SOURCES.md G33)",
             "derived": [{"file": str((assets / n).relative_to(ROOT)), "sha256": hashlib.sha256((assets / n).read_bytes()).hexdigest()}
                         for n in ("vineyard_fields.json", "vineyard_fields.png")]}
    m["datasets"] = [d for d in m["datasets"] if d.get("id") != did] + [entry]
    p.write_text(json.dumps(m, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    ap.add_argument("--zip", help="a DWR shapefile ZIP already on disk (one year; use with a single --years)")
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    if a.zip and len(a.years) != 1:
        ap.error("--zip takes one year")
    out = build(a.region, a.years, a.zip, a.offline)
    for y, v in out["years"].items():
        top = ", ".join(f"{k} {n}" for k, n in list(v["ava_acres"].items())[:4])
        c = v.get("cdl_compare")
        print(f"{y}: frame {v['frame_acres']} acres; {top}"
              + (f"  (CDL {c['cdl_year']}: frame {c['frame_acres']})" if c else ""))


if __name__ == "__main__":
    main()
