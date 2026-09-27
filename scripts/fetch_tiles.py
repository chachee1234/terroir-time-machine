#!/usr/bin/env python3
"""Finer modern terrain from the AWS Open Data "Terrain Tiles" (Mapzen/Tilezen Terrarium PNGs).

Tier 0, stdlib only. In the United States the tiles at zoom 13 carry USGS 3DEP 1/3 arc-second
(~10 m) elevation resampled to ~15 m pixels; offshore they carry NOAA ETOPO1 bathymetry. The
host (s3.amazonaws.com) is reachable from the cloud sandbox, unlike the 3DEP ImageServer, so
this replaces the manual Mac step for detail products. Tiles are cached, not committed:

  data/raw/tiles/terrarium/<z>/<x>/<y>.png   untouched tiles (git-ignored)
  data/manifest.json                         one entry per product: template, zoom, tile count, SHA-256
  <assets_dir>/dem_hi.{bin,json}             finer shading grid for the whole region frame
  <assets_dir>/detail/<id>.{bin,json}        one close-up grid per sub-AVA (Napa Valley's 16) and per
                                             extra "close_ups" entry in the region file
  <assets_dir>/detail/index.json             list of close-up locations for the viewer

Grids are Int16, little-endian, row 0 = north, on NAD83 / UTM zone 10N cells; the value times
`scale` (0.1) is metres. Usage:

  fetch_tiles.py --region data/regions/napa_valley.json [--zoom 13] [--hi-cells 1024]
                 [--detail-cell 15] [--detail-max 512] [--offline]
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import math
import struct
import subprocess
import sys
import zlib
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_terrain import utm_from_geographic  # noqa: E402

TEMPLATE = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
RIGHTS = ("AWS Open Data Terrain Tiles (Mapzen/Tilezen). United States 3DEP (formerly NED) and global "
          "GMTED2010 and SRTM terrain data courtesy of the U.S. Geological Survey; global ETOPO1 terrain "
          "data U.S. National Oceanic and Atmospheric Administration. Public domain sources in this area; "
          "attribution per https://github.com/tilezen/joerd/blob/master/docs/attribution.md")
CACHE = ROOT / "data" / "raw" / "tiles" / "terrarium"
SCALE = 0.1  # stored value x SCALE = metres


def geographic_from_utm(e, n, zone=10):
    """GRS80 transverse Mercator inverse (Krüger series). Returns (lat, lon) in degrees."""
    a, f, k0 = 6378137.0, 1 / 298.257222101, 0.9996
    nn = f / (2 - f)
    A = a / (1 + nn) * (1 + nn**2 / 4 + nn**4 / 64)
    be = [nn / 2 - 2 * nn**2 / 3 + 37 * nn**3 / 96,
          nn**2 / 48 + nn**3 / 15,
          17 * nn**3 / 480]
    de = [2 * nn - 2 * nn**2 / 3 - 2 * nn**3,
          7 * nn**2 / 3 - 8 * nn**3 / 5,
          56 * nn**3 / 15]
    xi, eta = n / (k0 * A), (e - 500000) / (k0 * A)
    xp = xi - sum(be[j] * math.sin(2 * (j + 1) * xi) * math.cosh(2 * (j + 1) * eta) for j in range(3))
    ep = eta - sum(be[j] * math.cos(2 * (j + 1) * xi) * math.sinh(2 * (j + 1) * eta) for j in range(3))
    chi = math.asin(math.sin(xp) / math.cosh(ep))
    lat = chi + sum(de[j] * math.sin(2 * (j + 1) * chi) for j in range(3))
    lon = math.radians(zone * 6 - 183) + math.atan2(math.sinh(ep), math.cos(xp))
    return math.degrees(lat), math.degrees(lon)


def merc_px(lat, lon, z):
    """Global Web Mercator pixel coordinates (256 px tiles) at zoom z."""
    s = 256 * 2**z
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return (lon + 180) / 360 * s, (1 - y / math.pi) / 2 * s


def decode_png_rgb(buf):
    """Minimal PNG decoder for 8-bit RGB/RGBA non-interlaced images (what Terrarium serves)."""
    if buf[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, w = 8, [], 0
    while pos < len(buf):
        (ln,) = struct.unpack(">I", buf[pos:pos + 4])
        typ, data = buf[pos + 4:pos + 8], buf[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", data)
            if depth != 8 or ctype not in (2, 6) or inter:
                raise ValueError("unsupported PNG layout")
            bpp = 3 if ctype == 2 else 4
        elif typ == b"IDAT":
            idat.append(data)
        elif typ == b"IEND":
            break
    raw, stride = zlib.decompress(b"".join(idat)), w * bpp
    out, prev = bytearray(stride * h), bytearray(stride)
    for r in range(h):
        ft, line = raw[r * (stride + 1)], bytearray(raw[r * (stride + 1) + 1:(r + 1) * (stride + 1)])
        if ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ft == 2:
            line = bytearray((x + y) & 255 for x, y in zip(line, prev))
        elif ft == 3:
            for i in range(stride):
                line[i] = (line[i] + ((line[i - bpp] if i >= bpp else 0) + prev[i]) // 2) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b, c = prev[i], (prev[i - bpp] if i >= bpp else 0)
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        out[r * stride:(r + 1) * stride] = line
        prev = line
    return w, h, bpp, out


def terrarium_heights(buf):
    w, h, bpp, px = decode_png_rgb(buf)
    return array("f", (px[i] * 256 + px[i + 1] + px[i + 2] / 256 - 32768 for i in range(0, w * h * bpp, bpp)))


def fetch(z, x, y, offline=False):
    path = CACHE / str(z) / str(x) / f"{y}.png"
    if not path.exists():
        if offline:
            raise SystemExit(f"missing cached tile {path} (--offline)")
        path.parent.mkdir(parents=True, exist_ok=True)
        url = TEMPLATE.format(z=z, x=x, y=y)
        subprocess.run(["curl", "-sSf", "--retry", "3", "-m", "60", "-o", str(path), url], check=True)
    return path


class Mosaic:
    """Lazily decoded tiles with bilinear sampling across tile edges."""

    def __init__(self, z, offline=False):
        self.z, self.offline, self.tiles, self.files = z, offline, {}, {}

    def prefetch(self, tiles):
        todo = [t for t in tiles if t not in self.files]
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            for t, p in zip(todo, ex.map(lambda t: fetch(self.z, *t, offline=self.offline), todo)):
                self.files[t] = p

    def tile(self, tx, ty):
        key = (tx, ty)
        if key not in self.tiles:
            if key not in self.files:
                self.files[key] = fetch(self.z, tx, ty, self.offline)
            self.tiles[key] = terrarium_heights(self.files[key].read_bytes())
        return self.tiles[key]

    def px(self, gx, gy):
        tx, ty = gx >> 8, gy >> 8
        return self.tile(tx, ty)[(gy & 255) * 256 + (gx & 255)]

    def sample(self, lat, lon):
        x, y = merc_px(lat, lon, self.z)
        x, y = x - 0.5, y - 0.5
        x0, y0 = int(math.floor(x)), int(math.floor(y))
        fx, fy = x - x0, y - y0
        a, b = self.px(x0, y0), self.px(x0 + 1, y0)
        c, d = self.px(x0, y0 + 1), self.px(x0 + 1, y0 + 1)
        return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

    def digest(self):
        h = hashlib.sha256()
        for key in sorted(self.files):
            h.update(f"{key[0]}/{key[1]}:".encode())
            h.update(hashlib.sha256(self.files[key].read_bytes()).digest())
        return h.hexdigest()


def tiles_for_bbox(bbox, z):
    """Tile indices covering a UTM bbox (corners and edge midpoints, plus one tile margin)."""
    e0, n0, e1, n1 = bbox
    pts = [geographic_from_utm(e, n) for e in (e0, (e0 + e1) / 2, e1) for n in (n0, (n0 + n1) / 2, n1)]
    xs, ys = zip(*(merc_px(la, lo, z) for la, lo in pts))
    return [(tx, ty) for tx in range(int(min(xs)) // 256 - 1, int(max(xs)) // 256 + 2)
            for ty in range(int(min(ys)) // 256 - 1, int(max(ys)) // 256 + 2)]


def grid_shape(bbox, long_cells=None, cell=None, max_cells=None):
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if cell is None:
        cell = max(w, h) / (long_cells - 1)
    if max_cells:
        cell = max(cell, max(w, h) / (max_cells - 1))
    return int(round(w / cell)) + 1, int(round(h / cell)) + 1


def sample_grid(mos, bbox, cols, rows):
    e0, n0, e1, n1 = bbox
    out = array("h")
    lo, hi = 1e9, -1e9
    for r in range(rows):
        n = n1 - (n1 - n0) * r / (rows - 1)
        for c in range(cols):
            e = e0 + (e1 - e0) * c / (cols - 1)
            v = mos.sample(*geographic_from_utm(e, n))
            lo, hi = min(lo, v), max(hi, v)
            out.append(max(-32767, min(32767, int(round(v / SCALE)))))
    if sys.byteorder != "little":
        out.byteswap()
    return out, lo, hi


def write_grid(path, grid, meta):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = grid.tobytes()
    path.with_suffix(".bin").write_bytes(data)
    meta["sha256"] = hashlib.sha256(data).hexdigest()
    path.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


def ava_features(region):
    g = json.loads((ROOT / region["boundary"]).read_text())
    for f in g["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        yield f["properties"], [c for poly in polys for ring in poly for c in ring]


def close_up_features(region):
    """Extra close-ups named in the region file: {"id", "name", "center_utm", "half_m"}."""
    for q in region.get("close_ups", []):
        cx, cy, h = q["center_utm"][0], q["center_utm"][1], q["half_m"]
        yield {"ava_id": q["id"], "name": q["name"], "kind": "place"}, [cx - h, cy - h, cx + h, cy + h]


def clip(b, frame):
    return [max(b[0], frame[0]), max(b[1], frame[1]), min(b[2], frame[2]), min(b[3], frame[3])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--zoom", type=int, default=13)
    ap.add_argument("--hi-cells", type=int, default=1024, help="long side of the region shading grid")
    ap.add_argument("--detail-cell", type=float, default=15.0, help="close-up cell size (m)")
    ap.add_argument("--detail-max", type=int, default=512, help="max close-up cells per side")
    ap.add_argument("--detail-pad", type=float, default=1500.0, help="padding around each sub-AVA (m)")
    ap.add_argument("--offline", action="store_true", help="use cached tiles only")
    a = ap.parse_args()

    region = json.loads((ROOT / a.region).read_text())
    rid, frame, assets = region["id"], region["bbox_utm"], ROOT / region["assets_dir"]
    today = datetime.date.today().isoformat()
    mos = Mosaic(a.zoom, a.offline)
    mos.prefetch(tiles_for_bbox(frame, a.zoom))
    common = {"source": "AWS Open Data Terrain Tiles, Terrarium encoding", "tile_template": TEMPLATE,
              "zoom": a.zoom, "rights": RIGHTS, "fetched": today,
              "horizontal_crs": "EPSG:26910 (NAD83 / UTM zone 10N); tiles are WGS84 Web Mercator, datum shift (~1 m) ignored",
              "encoding": "Int16 little-endian, row 0 = north", "scale": SCALE,
              "resampling": "bilinear from the tile mosaic at each UTM cell centre"}

    cols, rows = grid_shape(frame, long_cells=a.hi_cells)
    print(f"{rid}: shading grid {cols}x{rows} from {len(mos.files)} z{a.zoom} tiles", flush=True)
    grid, lo, hi = sample_grid(mos, frame, cols, rows)
    products = [write_grid(assets / "dem_hi", grid, dict(common, product="region shading grid", region=rid,
                bbox_utm=frame, cols=cols, rows=rows, cell_m=round((frame[2] - frame[0]) / (cols - 1), 3),
                range_m=[round(lo, 2), round(hi, 2)]))]

    index = []
    feats = []
    for props, coords in ava_features(region):
        if props["ava_id"] != rid:
            us = [utm_from_geographic(la, lo_) for lo_, la in coords]
            feats.append((dict(props, kind="ava"), [min(u[0] for u in us), min(u[1] for u in us),
                                                    max(u[0] for u in us), max(u[1] for u in us)], a.detail_pad))
    feats += [(p, b, 0.0) for p, b in close_up_features(region)]
    for props, b, pad in feats:
        aid = props["ava_id"]
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        half = max(b[2] - b[0], b[3] - b[1]) / 2 + pad
        half = max(half, 3000.0)
        box = clip([cx - half, cy - half, cx + half, cy + half], frame)
        box = [round(v, 1) for v in box]
        cols, rows = grid_shape(box, cell=a.detail_cell, max_cells=a.detail_max)
        mos.prefetch(tiles_for_bbox(box, a.zoom))
        grid, lo, hi = sample_grid(mos, box, cols, rows)
        cell = round((box[2] - box[0]) / (cols - 1), 3)
        print(f"  {aid}: {cols}x{rows} @ {cell} m, {lo:.0f}..{hi:.0f} m", flush=True)
        products.append(write_grid(assets / "detail" / aid, grid, dict(common, product="sub-AVA close-up",
                        region=rid, ava_id=aid, name=props["name"], bbox_utm=box, ava_bbox_utm=[round(v, 1) for v in b],
                        cols=cols, rows=rows, cell_m=cell, range_m=[round(lo, 2), round(hi, 2)])))
        index.append({"id": aid, "name": props["name"], "kind": props["kind"], "file": f"detail/{aid}", "bbox_utm": box,
                      "ava_bbox_utm": [round(v, 1) for v in b], "cols": cols, "rows": rows, "cell_m": cell})
    index.sort(key=lambda q: -q["bbox_utm"][3])
    (assets / "detail" / "index.json").write_text(json.dumps(
        {"region": rid, "source": common["source"], "rights": RIGHTS, "locations": index}, indent=1) + "\n")

    man_path = ROOT / "data" / "manifest.json"
    man = json.loads(man_path.read_text()) if man_path.exists() else {}
    entries = man.setdefault("datasets", [])
    mid = f"{rid}-terrain-tiles-z{a.zoom}"
    entries[:] = [e for e in entries if e.get("id") != mid]
    entries.append({"id": mid, "source": common["source"], "url_template": TEMPLATE, "zoom": a.zoom,
                    "tiles": len(mos.files), "tiles_sha256": mos.digest(), "fetched": today, "rights": RIGHTS,
                    "derived": [{"file": str((assets / ("dem_hi" if p["product"] == "region shading grid" else
                                  "detail/" + p["ava_id"])).relative_to(ROOT)) + ".bin", "sha256": p["sha256"]}
                                 for p in products]})
    man_path.write_text(json.dumps(man, indent=2) + "\n")
    print(f"{len(products)} grids written, {len(mos.files)} tiles, manifest id {mid}")


if __name__ == "__main__":
    main()
