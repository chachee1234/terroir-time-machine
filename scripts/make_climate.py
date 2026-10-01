#!/usr/bin/env python3
"""Climate normals for a region frame from PRISM (800 m, 1991-2020 normals, Oregon State University).

Tier 0, standard library only. PRISM serves each normal as one GeoTIFF for the whole lower 48 states (about
60 MB zipped; services.nacse.org/prism/data/get/normals/us/800m/<variable>/<period>). There is no smaller
download, so each file is fetched once to data/raw/prism/ (git-ignored), its SHA-256 goes into the output,
and only the 512 x 512 tiles that touch the frame are decoded (TIFF LZW, read here without GDAL).

Layers kept (the minimum for the viewer's climate card):
  ppt_mm        annual precipitation
  tmean_c, tmin_c, tmax_c   annual mean, mean daily minimum, mean daily maximum temperature
  gdd_f         growing degree days, April-October, base 50 F, from the monthly mean temperatures
                (the Winkler index; months x days, so a normals-based estimate, not a daily sum)

Output: <assets_dir>/climate.json
  {"source", "rights", "grid": {"lon0", "lat0", "dlon", "dlat", "cols", "rows"}, "layers": {name: [row-major,
  north row first, null outside data]}, "files": {...sha256}}

Rights: PRISM Climate Group, Oregon State University, https://prism.oregonstate.edu. Free to use with
that credit (PRISM terms of use). SOURCES.md G29.

Usage: make_climate.py --region data/regions/napa_valley.json [--offline]
"""
import argparse
import calendar
import datetime
import hashlib
import io
import json
import struct
import sys
import urllib.request
import zipfile
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_tiles import geographic_from_utm  # noqa: E402

URL = "https://services.nacse.org/prism/data/get/normals/us/800m/{var}/{period}"
CACHE = ROOT / "data" / "raw" / "prism"
GDD_MONTHS = range(4, 11)        # April to October
SOURCE = ("PRISM Climate Group, Oregon State University, 800 m 1991-2020 climate normals "
          "(https://prism.oregonstate.edu)")
RIGHTS = "Free to use with credit to the PRISM Climate Group, Oregon State University (PRISM terms of use)."


def fetch(var, period, offline=False):
    """Path of the cached zip for one normal, downloading it if needed."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"prism_{var}_{period}.zip"
    if not path.exists():
        if offline:
            raise SystemExit(f"{path} missing and --offline set")
        url = URL.format(var=var, period=period)
        print(f"downloading {url}", file=sys.stderr)
        req = urllib.request.Request(url, headers={"User-Agent": "terroir-time-machine"})
        with urllib.request.urlopen(req, timeout=600) as r:
            data = r.read()
        if not data.startswith(b"PK"):
            raise SystemExit(f"{url} did not return a zip: {data[:200]!r}")
        path.write_bytes(data)
    return path


def lzw_decode(data):
    """TIFF LZW (MSB-first codes, early change)."""
    out = bytearray()
    table = [bytes([i]) for i in range(256)] + [b"", b""]
    bits, nbits, buf, pos, prev = 9, 0, 0, 0, None
    n = len(data)
    while True:
        while nbits < bits and pos < n:
            buf = (buf << 8) | data[pos]
            pos += 1
            nbits += 8
        if nbits < bits:
            break
        nbits -= bits
        code = (buf >> nbits) & ((1 << bits) - 1)
        buf &= (1 << nbits) - 1
        if code == 256:
            table = table[:258]
            bits, prev = 9, None
            continue
        if code == 257:
            break
        if prev is None:
            entry = table[code]
        elif code < len(table):
            entry = table[code]
            table.append(prev + entry[:1])
        else:
            entry = prev + prev[:1]
            table.append(entry)
        out += entry
        prev = entry
        if len(table) + 1 >= (1 << bits) and bits < 12:
            bits += 1
    return bytes(out)


class Tiff:
    """Just enough of a GeoTIFF reader for PRISM: one band, float32, tiled, LZW or none, no predictor."""
    TYPES = {1: "B", 2: "s", 3: "H", 4: "I", 11: "f", 12: "d", 16: "Q"}

    def __init__(self, data):
        self.d = data
        bo = "<" if data[:2] == b"II" else ">"
        self.bo = bo
        off = struct.unpack(bo + "I", data[4:8])[0]
        n = struct.unpack(bo + "H", data[off:off + 2])[0]
        tags = {}
        for i in range(n):
            t, ty, c, v = struct.unpack(bo + "HHII", data[off + 2 + 12 * i: off + 14 + 12 * i])
            size = struct.calcsize(self.TYPES[ty]) * c
            raw = data[off + 10 + 12 * i: off + 14 + 12 * i] if size <= 4 else data[v:v + size]
            tags[t] = raw if ty == 2 else struct.unpack(bo + self.TYPES[ty] * c, raw[:size])
        self.w, self.h = tags[256][0], tags[257][0]
        self.tw, self.th = tags[322][0], tags[323][0]
        self.comp, self.pred = tags[259][0], tags.get(317, (1,))[0]
        if tags[258][0] != 32 or tags.get(339, (3,))[0] != 3 or self.comp not in (1, 5) or self.pred != 1:
            raise SystemExit("unexpected PRISM TIFF layout (want float32, LZW or none, no predictor)")
        self.offsets, self.counts = tags[324], tags[325]
        sx, sy = tags[33550][:2]
        _, _, _, X, Y, _ = tags[33922][:6]
        self.lon0, self.lat0, self.dlon, self.dlat = X, Y, sx, sy   # north-west corner of the north-west cell
        self.across = (self.w + self.tw - 1) // self.tw
        self.cache = {}

    def tile(self, tr, tc):
        k = (tr, tc)
        if k not in self.cache:
            i = tr * self.across + tc
            raw = self.d[self.offsets[i]: self.offsets[i] + self.counts[i]]
            if self.comp == 5:
                raw = lzw_decode(raw)
            a = array("f")
            a.frombytes(raw[:self.tw * self.th * 4])
            if (self.bo == ">") != (sys.byteorder == "big"):
                a.byteswap()
            self.cache[k] = a
        return self.cache[k]

    def value(self, row, col):
        if not (0 <= row < self.h and 0 <= col < self.w):
            return None
        v = self.tile(row // self.th, col // self.tw)[(row % self.th) * self.tw + col % self.tw]
        return None if v < -9000 else v


def read_normal(var, period, offline=False):
    path = fetch(var, period, offline)
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.endswith(".tif"))
        tif = Tiff(z.read(name))
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return tif, {"file": name, "url": URL.format(var=var, period=period), "sha256": sha}


def frame_window(region, tif, pad=1):
    """PRISM row/column window covering the region's UTM frame, as (r0, c0, rows, cols)."""
    x0, y0, x1, y1 = region["bbox_utm"]
    corners = [geographic_from_utm(e, n) for e in (x0, x1) for n in (y0, y1)]
    lats, lons = [c[0] for c in corners], [c[1] for c in corners]
    c0 = int((min(lons) - tif.lon0) / tif.dlon) - pad
    c1 = int((max(lons) - tif.lon0) / tif.dlon) + pad
    r0 = int((tif.lat0 - max(lats)) / tif.dlat) - pad
    r1 = int((tif.lat0 - min(lats)) / tif.dlat) + pad
    return r0, c0, r1 - r0 + 1, c1 - c0 + 1


def clip(tif, win):
    r0, c0, rows, cols = win
    return [tif.value(r0 + r, c0 + c) for r in range(rows) for c in range(cols)]


def winkler_class(gdd_f):
    """UC Davis Winkler region for a growing-degree-day total (F, April-October)."""
    for lim, name in ((2500, "Region I"), (3000, "Region II"), (3500, "Region III"), (4000, "Region IV")):
        if gdd_f <= lim:
            return name
    return "Region V"


def build(region_path, offline=False):
    region = json.loads(Path(region_path).read_text())
    layers, files, win, grid = {}, {}, None, None
    for var, key in (("ppt", "ppt_mm"), ("tmean", "tmean_c"), ("tmin", "tmin_c"), ("tmax", "tmax_c")):
        tif, meta = read_normal(var, "annual", offline)
        files[f"{var}_annual"] = meta
        if win is None:
            win = frame_window(region, tif)
            r0, c0, rows, cols = win
            grid = {"lon0": round(tif.lon0 + c0 * tif.dlon, 6), "lat0": round(tif.lat0 - r0 * tif.dlat, 6),
                    "dlon": tif.dlon, "dlat": tif.dlat, "cols": cols, "rows": rows,
                    "note": "lon0/lat0 is the north-west corner of the north-west cell; NAD83 geographic"}
        layers[key] = [None if v is None else round(v, 1) for v in clip(tif, win)]
    gdd = [0.0] * (win[2] * win[3])
    for m in GDD_MONTHS:
        tif, meta = read_normal("tmean", f"{m:02d}", offline)
        files[f"tmean_{m:02d}"] = meta
        days = calendar.monthrange(2001, m)[1]
        for i, v in enumerate(clip(tif, win)):
            gdd[i] = None if v is None or gdd[i] is None else gdd[i] + max(0.0, v * 9 / 5 + 32 - 50) * days
    layers["gdd_f"] = [None if v is None else round(v) for v in gdd]
    out = {"source": SOURCE, "rights": RIGHTS, "built": datetime.date.today().isoformat(), "grid": grid,
           "layers": layers, "units": {"ppt_mm": "mm/year", "tmean_c": "C", "tmin_c": "C", "tmax_c": "C",
                                       "gdd_f": "F degree-days, Apr-Oct, base 50 F (Winkler index)"},
           "limits": "800 m cells: one value per cell, so a hillside and the valley floor beside it can share a "
                     "cell. 30-year averages, not any one year.", "files": files}
    path = ROOT / region["assets_dir"] / "climate.json"
    path.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    return out, path


def at(climate, lat, lon):
    """Climate values in the cell containing (lat, lon), or None outside the grid."""
    g = climate["grid"]
    c = int((lon - g["lon0"]) / g["dlon"])
    r = int((g["lat0"] - lat) / g["dlat"])
    if not (0 <= r < g["rows"] and 0 <= c < g["cols"]):
        return None
    i = r * g["cols"] + c
    vals = {k: v[i] for k, v in climate["layers"].items()}
    if vals.get("gdd_f") is not None:
        vals["winkler"] = winkler_class(vals["gdd_f"])
    vals["cell"] = {"lon": round(g["lon0"] + (c + 0.5) * g["dlon"], 5), "lat": round(g["lat0"] - (r + 0.5) * g["dlat"], 5)}
    return vals


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    out, path = build(a.region, a.offline)
    g = out["grid"]
    vals = [v for v in out["layers"]["gdd_f"] if v is not None]
    print(f"{path.relative_to(ROOT)}: {g['cols']} x {g['rows']} cells; GDD {min(vals)}..{max(vals)} F")


if __name__ == "__main__":
    main()
