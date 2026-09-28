#!/usr/bin/env python3
"""Satellite texture for a region's "Today" terrain from Sentinel-2 L2A true-colour imagery.

Tier 0, stdlib only (no GDAL, no numpy). Source: the Sentinel-2 L2A Cloud-Optimized GeoTIFFs in the AWS
Open Data bucket `sentinel-cogs` (the collection Earth Search serves; its STAC API is blocked from the
cloud sandbox, but each scene's STAC item sits in the bucket next to its images). Copernicus Sentinel
data are free and open; credit "Contains modified Copernicus Sentinel data <year>".

What it does, with no manual step:
  1. Finds the Sentinel-2 grid squares (MGRS, UTM zone 10) that cover the region frame.
  2. Lists the scenes of the chosen months (default June-September of the last two years) in the bucket,
     reads each scene's STAC item, and keeps scenes with no missing pixels over the square; picks the
     lowest cloud cover (the same acquisition date for every square when more than one is needed).
  3. Reads only the TCI (true-colour, 8-bit RGB) tiles it needs, from the overview closest to --cell,
     with HTTP range requests; decodes DEFLATE + horizontal predictor itself.
  4. Crops the frame (Sentinel-2 grids are WGS84 / UTM 10N; the frame is NAD83 / UTM 10N; the ~1 m
     datum difference is ignored) and writes a baseline JPEG plus a JSON record next to the terrain.

Outputs (per region):
  <assets>/imagery.jpg    true colour, north up, covering bbox_utm exactly
  <assets>/imagery.json   scene id, date, cloud cover, source URL, pixel size, bbox, credit
  data/manifest.json      one entry per region
  data/raw/sentinel2/     STAC items and decoded tiles are not kept; only the scene list cache

Usage:
  make_imagery_texture.py --region data/regions/napa_valley.json [--cell 40] [--months 6-9]
                          [--years 2025,2024] [--max-cloud 20] [--scene S2B_10SEH_20250811_0_L2A]
  make_imagery_texture.py --region data/regions/mt_st_helena.json     (the 30 km block, prototype/assets)
"""
import argparse
import concurrent.futures
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
BUCKET = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
PREFIX = "sentinel-s2-l2a-cogs"
CREDIT = "Contains modified Copernicus Sentinel data {year}, processed by ESA; Sentinel-2 L2A COGs from AWS Open Data (Element 84)"
RIGHTS = ("Copernicus Sentinel data: free, full and open access under the Copernicus data policy "
          "(Commission Delegated Regulation (EU) No 1159/2013); attribution required")


# ---------------------------------------------------------------- MGRS squares (UTM zone, 100 km letters)
def mgrs_square(e, n, zone=10):
    """100 km grid square letters of a UTM point (e.g. 'EH' for Napa)."""
    cols = ("ABCDEFGH", "JKLMNPQR", "STUVWXYZ")[(zone - 1) % 3]
    rows = "ABCDEFGHJKLMNPQRSTUV"
    return cols[int(e // 100000) - 1] + rows[(int(n // 100000) + (5 if zone % 2 == 0 else 0)) % 20]


def square_extent(e, n):
    """Sentinel-2 tile extent for the 100 km square holding (e, n): 109.8 km, origin 20 m west/north."""
    x0 = int(e // 100000) * 100000 - 20
    y1 = int(n // 100000) * 100000 + 100020
    return [x0, y1 - 109800, x0 + 109800, y1]


def squares_for(bbox, zone=10):
    """Fewest squares covering bbox: one if a single tile covers it, else every square a corner falls in."""
    e0, n0, e1, n1 = bbox
    for e, n in ((e0, n1), (e0, n0), (e1, n1), (e1, n0)):
        x0, y0, x1, y1 = square_extent(e, n)
        if x0 <= e0 and y0 <= n0 and x1 >= e1 and y1 >= n1:
            return [(mgrs_square(e, n, zone), [x0, y0, x1, y1])]
    out = {}
    for e, n in ((e0, n1), (e0, n0), (e1, n1), (e1, n0)):
        out.setdefault(mgrs_square(e, n, zone), square_extent(e, n))
    return sorted(out.items())


# ---------------------------------------------------------------- bucket access
def http(url, rng=None, timeout=60):
    req = urllib.request.Request(url, headers={"Range": f"bytes={rng[0]}-{rng[1]}"} if rng else {})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception:
            if attempt == 3:
                raise
    return b""


def list_prefixes(prefix):
    """Sub-folders of a bucket prefix (one listing page holds up to 1000, far more than a month of scenes)."""
    xml = http(f"{BUCKET}/?list-type=2&delimiter=/&prefix={prefix}").decode()
    return [p for p in re.findall(r"<Prefix>([^<]+/)</Prefix>", xml) if p != prefix]


def scene_items(zone, square, years, months):
    """STAC items of every scene of one square in the given years and months (fetched in parallel)."""
    band, sq = square[0], square[1]
    lat = "S"   # latitude band of Northern California (32-40 N); asserted against each item's bbox
    paths = []
    for y in years:
        for m in months:
            paths += list_prefixes(f"{PREFIX}/{zone}/{lat}/{band}{sq}/{y}/{m}/")

    def item(p):
        sid = p.rstrip("/").rsplit("/", 1)[1]
        try:
            return json.loads(http(f"{BUCKET}/{p}{sid}.json"))
        except Exception:
            return None
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        return [i for i in ex.map(item, paths) if i]


def pick_scene(items_by_square, max_cloud):
    """Lowest cloud cover, no missing pixels; all squares from the same date when there are several."""
    def ok(i):
        p = i["properties"]
        return p.get("s2:nodata_pixel_percentage", 0) <= 0.5 and p.get("eo:cloud_cover", 100) <= max_cloud
    by_date = {}
    for sq, items in items_by_square.items():
        for i in filter(ok, items):
            d = i["properties"]["datetime"][:10]
            best = by_date.setdefault(d, {}).get(sq)
            if best is None or i["properties"]["eo:cloud_cover"] < best["properties"]["eo:cloud_cover"]:
                by_date[d][sq] = i
    full = [(max(i["properties"]["eo:cloud_cover"] for i in s.values()), d, s)
            for d, s in by_date.items() if len(s) == len(items_by_square)]
    if not full:
        raise SystemExit(f"no scene with <= {max_cloud}% cloud and full coverage; widen --months, --years or --max-cloud")
    return min(full, key=lambda t: (t[0], [-ord(c) for c in t[1]]))   # least cloud, then most recent


# ---------------------------------------------------------------- Cloud-Optimized GeoTIFF reader
class RangeFile:
    """Byte access to a remote file through cached 64 KB range requests."""
    BLOCK = 65536

    def __init__(self, url):
        self.url, self.cache = url, {}

    def read(self, off, n):
        out = bytearray()
        while n > 0:
            b, o = divmod(off, self.BLOCK)
            if b not in self.cache:
                self.cache[b] = http(self.url, (b * self.BLOCK, b * self.BLOCK + self.BLOCK - 1))
            chunk = self.cache[b][o:o + n]
            if not chunk:
                raise ValueError("read past end of file")
            out += chunk
            off, n = off + len(chunk), n - len(chunk)
        return bytes(out)


TYPES = {1: ("B", 1), 2: ("c", 1), 3: ("H", 2), 4: ("I", 4), 16: ("Q", 8), 12: ("d", 8)}


def read_ifds(f):
    """All image file directories of a classic (not Big) TIFF: list of {tag: values}."""
    head = f.read(0, 8)
    bo = {b"II": "<", b"MM": ">"}[head[:2]]
    if struct.unpack(bo + "H", head[2:4])[0] != 42:
        raise ValueError("BigTIFF not supported")
    off, ifds = struct.unpack(bo + "I", head[4:8])[0], []
    while off:
        (n,) = struct.unpack(bo + "H", f.read(off, 2))
        raw = f.read(off + 2, 12 * n + 4)
        tags = {}
        for i in range(n):
            tag, typ, cnt, val = struct.unpack(bo + "HHI4s", raw[12 * i:12 * i + 12])
            if typ not in TYPES:
                continue
            code, size = TYPES[typ]
            data = val if size * cnt <= 4 else f.read(struct.unpack(bo + "I", val)[0], size * cnt)
            tags[tag] = struct.unpack(bo + code * cnt, data[:size * cnt]) if typ != 2 else data[:cnt]
        ifds.append(tags)
        (off,) = struct.unpack(bo + "I", raw[12 * n:12 * n + 4])
    return bo, ifds


def unpredict(buf, width, spp):
    """Undo TIFF horizontal differencing (predictor 2) for 8-bit chunky samples, row by row."""
    out = bytearray(buf)
    row = width * spp
    for r in range(0, len(out), row):
        for c in range(spp):
            acc = 0
            for i in range(r + c, r + row, spp):
                acc = (acc + out[i]) & 255
                out[i] = acc
    return out


def read_window(f, bo, ifd, col0, row0, cols, rows):
    """RGB bytes of a pixel window from one tiled, DEFLATE, 8-bit, 3-sample image directory."""
    w, h = ifd[256][0], ifd[257][0]
    tw, th = ifd[322][0], ifd[323][0]
    comp, pred, spp = ifd.get(259, (1,))[0], ifd.get(317, (1,))[0], ifd.get(277, (1,))[0]
    if comp not in (8, 32946) or spp != 3 or ifd[258][0] != 8:
        raise ValueError(f"unsupported TIFF layout (compression {comp}, samples {spp}, bits {ifd[258]})")
    across = math.ceil(w / tw)
    out = bytearray(cols * rows * 3)
    need = [(ty, tx) for ty in range(row0 // th, (row0 + rows - 1) // th + 1)
            for tx in range(col0 // tw, (col0 + cols - 1) // tw + 1)]

    def tile(k):
        ty, tx = k
        i = ty * across + tx
        raw = zlib.decompress(http(f.url, (ifd[324][i], ifd[324][i] + ifd[325][i] - 1)))
        return k, unpredict(raw, tw, spp) if pred == 2 else bytearray(raw)
    with concurrent.futures.ThreadPoolExecutor(8) as ex:
        for (ty, tx), px in ex.map(tile, need):
            for r in range(max(row0, ty * th), min(row0 + rows, ty * th + th, h)):
                c0, c1 = max(col0, tx * tw), min(col0 + cols, tx * tw + tw, w)
                if c1 <= c0:
                    continue
                s = ((r - ty * th) * tw + (c0 - tx * tw)) * 3
                d = ((r - row0) * cols + (c0 - col0)) * 3
                out[d:d + (c1 - c0) * 3] = px[s:s + (c1 - c0) * 3]
    return out


# ---------------------------------------------------------------- baseline JPEG encoder (JFIF, 4:4:4)
ZIGZAG = [0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21,
          28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61,
          54, 47, 55, 62, 63]
Q_LUM = [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51,
         87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92, 49, 64, 78, 87, 103, 121, 120, 101,
         72, 92, 95, 98, 112, 100, 103, 99]
Q_CHR = [17, 18, 24, 47] + [99] * 4 + [18, 21, 26, 66] + [99] * 4 + [24, 26, 56] + [99] * 5 + [47, 66] + [99] * 38
# Annex K typical Huffman tables: (code-length counts 1..16, symbols)
DC_LUM = ([0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0], list(range(12)))
DC_CHR = ([0, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0], list(range(12)))
AC_LUM = ([0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 0x7d], bytes.fromhex(
    "01020300041105122131410613516107227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a"
    "434445464748494a535455565758595a636465666768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9"
    "aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9fa"))
AC_CHR = ([0, 2, 1, 2, 4, 4, 3, 4, 7, 5, 4, 4, 0, 1, 2, 0x77], bytes.fromhex(
    "000102031104052131061241510761711322328108144291a1b1c109233352f0156272d10a162434e125f11718191a262728292a35363738"
    "393a434445464748494a535455565758595a636465666768696a737475767778797a82838485868788898a92939495969798999aa2a3a4a5a6"
    "a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae2e3e4e5e6e7e8e9eaf2f3f4f5f6f7f8f9fa"))
COS = [[(math.sqrt(0.5) if u == 0 else 1.0) * math.cos((2 * x + 1) * u * math.pi / 16) / 2 for x in range(8)] for u in range(8)]


def huff_codes(spec):
    counts, syms = spec
    codes, code, k = {}, 0, 0
    for length in range(1, 17):
        for _ in range(counts[length - 1]):
            codes[syms[k]] = (code, length)
            code, k = code + 1, k + 1
        code <<= 1
    return codes


def scaled_q(table, quality):
    s = 5000 / quality if quality < 50 else 200 - 2 * quality
    return [max(1, min(255, (q * s + 50) // 100)) for q in table]


class Bits:
    def __init__(self):
        self.out, self.acc, self.n = bytearray(), 0, 0

    def put(self, code, length):
        self.acc, self.n = (self.acc << length) | code, self.n + length
        while self.n >= 8:
            self.n -= 8
            b = (self.acc >> self.n) & 255
            self.out.append(b)
            if b == 255:
                self.out.append(0)
        self.acc &= (1 << self.n) - 1          # keep only the bits not yet written

    def flush(self):
        if self.n:
            self.put((1 << (8 - self.n)) - 1, 8 - self.n)


def magnitude(v):
    n = abs(v).bit_length()
    return n, (v if v >= 0 else v + (1 << n) - 1)


def encode_jpeg(rgb, w, h, quality=85):
    """Baseline sequential JPEG (JFIF, YCbCr 4:4:4, Annex K Huffman tables) from packed RGB bytes."""
    ql, qc = scaled_q(Q_LUM, quality), scaled_q(Q_CHR, quality)
    hdc, hac = (huff_codes(DC_LUM), huff_codes(DC_CHR)), (huff_codes(AC_LUM), huff_codes(AC_CHR))
    bits, pred = Bits(), [0, 0, 0]
    for by in range(0, h, 8):
        for bx in range(0, w, 8):
            planes = ([0.0] * 64, [0.0] * 64, [0.0] * 64)
            for y in range(8):
                r0 = (min(by + y, h - 1) * w) * 3
                for x in range(8):
                    i = r0 + min(bx + x, w - 1) * 3
                    r, g, b = rgb[i], rgb[i + 1], rgb[i + 2]
                    k = y * 8 + x
                    planes[0][k] = 0.299 * r + 0.587 * g + 0.114 * b - 128
                    planes[1][k] = -0.168736 * r - 0.331264 * g + 0.5 * b
                    planes[2][k] = 0.5 * r - 0.418688 * g - 0.081312 * b
            for ch, blk in enumerate(planes):
                q = ql if ch == 0 else qc
                tmp = [sum(COS[u][x] * blk[y * 8 + x] for x in range(8)) for y in range(8) for u in range(8)]
                coef = [sum(COS[v][y] * tmp[y * 8 + u] for y in range(8)) for v in range(8) for u in range(8)]
                zz = [int(round(coef[ZIGZAG[k]] / q[ZIGZAG[k]])) for k in range(64)]
                t = 0 if ch == 0 else 1
                diff, pred[ch] = zz[0] - pred[ch], zz[0]
                n, v = magnitude(diff)
                bits.put(*hdc[t][n])
                if n:
                    bits.put(v, n)
                run = 0
                for k in range(1, 64):
                    if zz[k] == 0:
                        run += 1
                        continue
                    while run > 15:
                        bits.put(*hac[t][0xF0])
                        run -= 16
                    n, v = magnitude(zz[k])
                    bits.put(*hac[t][(run << 4) | n])
                    bits.put(v, n)
                    run = 0
                if run:
                    bits.put(*hac[t][0x00])
    bits.flush()

    def seg(marker, data):
        return bytes([0xFF, marker]) + struct.pack(">H", len(data) + 2) + data
    dqt = seg(0xDB, bytes([0]) + bytes(ql[ZIGZAG[k]] for k in range(64)) + bytes([1]) + bytes(qc[ZIGZAG[k]] for k in range(64)))
    sof = seg(0xC0, struct.pack(">BHHB", 8, h, w, 3) + bytes([1, 0x11, 0, 2, 0x11, 1, 3, 0x11, 1]))
    dht = seg(0xC4, b"".join(bytes([cls_id]) + bytes(spec[0]) + bytes(spec[1]) for cls_id, spec in
                             ((0x00, DC_LUM), (0x10, AC_LUM), (0x01, DC_CHR), (0x11, AC_CHR))))
    sos = seg(0xDA, bytes([3, 1, 0x00, 2, 0x11, 3, 0x11, 0, 63, 0]))
    app0 = seg(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
    return b"\xff\xd8" + app0 + dqt + sof + dht + sos + bytes(bits.out) + b"\xff\xd9"


# ---------------------------------------------------------------- build
def frame_of(region):
    """(bbox, assets dir) for a region file; the 30 km block's assets live in prototype/assets."""
    assets = ROOT / region.get("assets_dir", "prototype/assets")
    bbox = region.get("bbox_utm")
    if not bbox:
        bbox = json.loads((assets / "terrain.json").read_text())["aoi"]["bbox_utm"]
    return [float(v) for v in bbox], assets


def build(region, cell=40.0, years=None, months=range(6, 10), max_cloud=20.0, scene=None, quality=85, log=print):
    bbox, assets = frame_of(region)
    zone = int(region.get("utm_zone", 10))
    squares = squares_for(bbox, zone)
    if years is None:
        y = datetime.date.today().year
        years = [y, y - 1]
    if scene:
        m = re.fullmatch(r"(S2[ABC])_(\d{2})([A-Z])([A-Z]{2})_(\d{4})(\d{2})(\d{2})_(\d)_L2A", scene)
        if not m:
            raise SystemExit(f"not a Sentinel-2 L2A scene id: {scene}")
        z, lat, sq, yy, mm = m.group(2), m.group(3), m.group(4), m.group(5), int(m.group(6))
        items = {sq: [json.loads(http(f"{BUCKET}/{PREFIX}/{int(z)}/{lat}/{sq}/{yy}/{mm}/{scene}/{scene}.json"))]}
        if [s for s, _ in squares] != [sq]:
            raise SystemExit(f"{scene} does not cover the whole frame; squares needed: {[s for s, _ in squares]}")
        chosen = {sq: items[sq][0]}
        cloud, date = chosen[sq]["properties"]["eo:cloud_cover"], chosen[sq]["properties"]["datetime"][:10]
    else:
        items = {}
        for sq, _ in squares:
            items[sq] = scene_items(zone, sq, years, list(months))
            log(f"  square {zone}S{sq}: {len(items[sq])} scenes in {years} months {list(months)}")
        cloud, date, chosen = pick_scene(items, max_cloud)
    log(f"  scene date {date}, cloud cover {cloud:.2f}%: " + ", ".join(i["id"] for i in chosen.values()))

    e0, n0, e1, n1 = bbox
    cols, rows = int(round((e1 - e0) / cell)), int(round((n1 - n0) / cell))
    rgb = bytearray(cols * rows * 3)
    sources = []
    for sq, ext in squares:
        it = chosen[sq]
        url = it["assets"]["visual"]["href"]
        f = RangeFile(url)
        bo, ifds = read_ifds(f)
        full = ifds[0][256][0]
        # the overview whose pixel is closest to the requested cell (10, 20, 40, 80, 160 m)
        lvl = min(range(len(ifds)), key=lambda k: abs(math.log((10.0 * full / ifds[k][256][0]) / cell)))
        ifd = ifds[lvl]
        px = 10.0 * full / ifd[256][0]
        tx0, ty1 = it["assets"]["visual"]["proj:transform"][2], it["assets"]["visual"]["proj:transform"][5]
        # window of this square inside the frame, in overview pixels
        c0 = max(0, int(math.floor((e0 - tx0) / px)))
        r0 = max(0, int(math.floor((ty1 - n1) / px)))
        c1 = min(ifd[256][0], int(math.ceil((e1 - tx0) / px)))
        r1 = min(ifd[257][0], int(math.ceil((ty1 - n0) / px)))
        win = read_window(f, bo, ifd, c0, r0, c1 - c0, r1 - r0)
        ww = c1 - c0
        log(f"  {it['id']}: overview {lvl} ({px:g} m), window {ww}x{r1 - r0} px")
        # nearest-neighbour resample of the window onto the output cells (cell centres)
        for r in range(rows):
            n = n1 - (r + 0.5) * (n1 - n0) / rows
            sr = int((ty1 - n) / px) - r0
            if not 0 <= sr < r1 - r0:
                continue
            base, srow = r * cols * 3, sr * ww * 3
            for c in range(cols):
                e = e0 + (c + 0.5) * (e1 - e0) / cols
                sc = int((e - tx0) / px) - c0
                if 0 <= sc < ww:
                    s = srow + sc * 3
                    if win[s] or win[s + 1] or win[s + 2]:
                        rgb[base + c * 3:base + c * 3 + 3] = win[s:s + 3]
        sources.append({"scene": it["id"], "href": url, "overview": lvl, "pixel_m": px,
                        "cloud_cover": it["properties"]["eo:cloud_cover"], "datetime": it["properties"]["datetime"]})
    missing = sum(1 for k in range(0, len(rgb), 3) if not (rgb[k] or rgb[k + 1] or rgb[k + 2]))
    jpg = encode_jpeg(rgb, cols, rows, quality)
    out = assets / "imagery.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(jpg)
    year = date[:4]
    meta = {"label": f"Sentinel-2 true colour, {date}", "credit": CREDIT.format(year=year), "rights": RIGHTS,
            "class": "measured-approx", "source": "Sentinel-2 L2A TCI (B04, B03, B02), Cloud-Optimized GeoTIFFs",
            "bucket": BUCKET + "/" + PREFIX, "scenes": sources, "date": date,
            "cloud_cover_percent": round(cloud, 2), "months": list(months), "max_cloud": max_cloud,
            "image": {"file": out.name, "sha256": hashlib.sha256(jpg).hexdigest(), "width": cols, "height": rows,
                      "cell_m": [round((e1 - e0) / cols, 3), round((n1 - n0) / rows, 3)], "bbox_utm": bbox,
                      "crs": f"EPSG:269{zone:02d} frame; imagery WGS84 / UTM {zone}N, datum difference (~1 m) ignored",
                      "resampling": "nearest overview pixel at each cell centre", "missing_cells": missing,
                      "encoding": f"baseline JPEG, quality {quality}, row 0 = north"},
            "limits": "One summer acquisition: shadows and colours are that day's; 8-bit TCI stretch as delivered by ESA; "
                      "clouds in the scene (see cloud_cover_percent) are not masked."}
    (assets / "imagery.json").write_text(json.dumps(meta, indent=1) + "\n")
    log(f"  wrote {out.relative_to(ROOT)} {cols}x{rows} ({len(jpg) / 1e6:.2f} MB), {missing} empty cells")
    return meta


def register(region, meta):
    mp = ROOT / "data" / "manifest.json"
    man = json.loads(mp.read_text()) if mp.exists() else {"datasets": []}
    mid = f"{region['id']}-sentinel2-imagery"
    _, assets = frame_of(region)
    man["datasets"] = [d for d in man["datasets"] if d.get("id") != mid]
    man["datasets"].append({"id": mid, "source": meta["source"], "url": meta["bucket"],
                            "scenes": [s["scene"] for s in meta["scenes"]], "date": meta["date"],
                            "fetched": datetime.date.today().isoformat(), "rights": meta["rights"], "credit": meta["credit"],
                            "derived": [{"file": str((assets / "imagery.jpg").relative_to(ROOT)), "sha256": meta["image"]["sha256"]}]})
    mp.write_text(json.dumps(man, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True, help="region file in data/regions/")
    ap.add_argument("--cell", type=float, default=40.0, help="output pixel size in metres (nearest overview is read)")
    ap.add_argument("--months", default="6-9", help="month range to search, e.g. 6-9 (dry season)")
    ap.add_argument("--years", help="comma-separated years to search (default: this year and last)")
    ap.add_argument("--max-cloud", type=float, default=20.0, help="largest scene cloud cover accepted (%%)")
    ap.add_argument("--scene", help="use this scene id instead of searching (pins the result)")
    ap.add_argument("--quality", type=int, default=85, help="JPEG quality")
    a = ap.parse_args()
    region = json.loads((ROOT / a.region).read_text())
    m0, m1 = (int(v) for v in a.months.split("-"))
    years = [int(y) for y in a.years.split(",")] if a.years else None
    print(f"{region['id']}: Sentinel-2 texture at {a.cell:g} m")
    meta = build(region, a.cell, years, range(m0, m1 + 1), a.max_cloud, a.scene, a.quality)
    register(region, meta)


if __name__ == "__main__":
    main()
