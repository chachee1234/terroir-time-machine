#!/usr/bin/env python3
"""Fetch the modern-terrain DEM for the ~30 km AOI around the GNIS point.

Tier 0, stdlib only. One request to the USGS 3DEP ImageServer exportImage
endpoint in NAD83 / UTM zone 10N (EPSG:26910), then:
  data/raw/mt_st_helena_3dep_<n>m.tif     untouched response (git-ignored)
  data/manifest.json                      URL, parameters, SHA-256, CRS
  prototype/assets/terrain.bin            downsampled Int16 heightfield (m)
  prototype/assets/terrain.json           grid metadata + provenance

Usage: fetch_terrain.py [--size 1000] [--out-cells 240] [--from-raw]
"""
import argparse
import datetime
import hashlib
import json
import math
import struct
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICE = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer"
GNIS_ID = 232163
GNIS_LAT, GNIS_LON = 38.6691784, -122.6333914  # NAD83, official GNIS record
AOI_HALF_M = 15000  # 30 km square design extent (PROJECT.md), not a geological boundary
EPSG = 26910


def utm_from_geographic(lat, lon, zone=10):
    """GRS80 transverse Mercator forward (Krüger series). Returns (easting, northing)."""
    a, f, k0 = 6378137.0, 1 / 298.257222101, 0.9996
    n = f / (2 - f)
    A = a / (1 + n) * (1 + n**2 / 4 + n**4 / 64)
    al = [n / 2 - 2 * n**2 / 3 + 5 * n**3 / 16,
          13 * n**2 / 48 - 3 * n**3 / 5,
          61 * n**3 / 240]
    phi, lam = math.radians(lat), math.radians(lon - (zone * 6 - 183))
    e = 2 * math.sqrt(n) / (1 + n)
    t = math.sinh(math.atanh(math.sin(phi)) - e * math.atanh(e * math.sin(phi)))
    xi, eta = math.atan2(t, math.cos(lam)), math.atanh(math.sin(lam) / math.sqrt(1 + t * t))
    x = eta + sum(al[j] * math.cos(2 * (j + 1) * xi) * math.sinh(2 * (j + 1) * eta) for j in range(3))
    y = xi + sum(al[j] * math.sin(2 * (j + 1) * xi) * math.cosh(2 * (j + 1) * eta) for j in range(3))
    return 500000 + k0 * A * x, k0 * A * y


def read_float_tiff(buf):
    """Minimal reader for an uncompressed single-band Float32 GeoTIFF (strips or tiles)."""
    bo = {b"II": "<", b"MM": ">"}[buf[:2]]
    (ifd,) = struct.unpack(bo + "I", buf[4:8])
    (count,) = struct.unpack(bo + "H", buf[ifd:ifd + 2])
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 11: 4, 12: 8, 16: 8}
    codes = {1: "B", 2: "c", 3: "H", 4: "I", 11: "f", 12: "d", 16: "Q"}
    tags = {}
    for i in range(count):
        off = ifd + 2 + 12 * i
        tag, typ, n = struct.unpack(bo + "HHI", buf[off:off + 8])
        if typ not in codes:
            continue
        size = sizes[typ] * n
        data = buf[off + 8:off + 12] if size <= 4 else buf[struct.unpack(bo + "I", buf[off + 8:off + 12])[0]:][:size]
        tags[tag] = struct.unpack(bo + codes[typ] * n, data[:size]) if typ != 2 else data[:size]
    w, h = tags[256][0], tags[257][0]
    if tags.get(259, (1,))[0] != 1 or tags[258][0] != 32 or tags.get(339, (1,))[0] != 3:
        raise ValueError(f"unsupported TIFF (compression={tags.get(259)}, bits={tags[258]}, format={tags.get(339)})")
    out = [0.0] * (w * h)
    if 322 in tags:  # tiled
        tw, th = tags[322][0], tags[323][0]
        across = math.ceil(w / tw)
        for k, (o, c) in enumerate(zip(tags[324], tags[325])):
            vals = struct.unpack(bo + "f" * (c // 4), buf[o:o + c])
            ty, tx = divmod(k, across)
            for r in range(th):
                y = ty * th + r
                if y >= h:
                    break
                for cc in range(tw):
                    x = tx * tw + cc
                    if x < w:
                        out[y * w + x] = vals[r * tw + cc]
    else:
        pos = 0
        for o, c in zip(tags[273], tags[279]):
            vals = struct.unpack(bo + "f" * (c // 4), buf[o:o + c])
            out[pos:pos + len(vals)] = vals
            pos += len(vals)
    return w, h, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", type=int, default=1000, help="request width/height in pixels")
    ap.add_argument("--out-cells", type=int, default=240, help="browser heightfield width/height")
    ap.add_argument("--from-raw", action="store_true", help="reuse the saved response")
    args = ap.parse_args()

    cx, cy = utm_from_geographic(GNIS_LAT, GNIS_LON)
    bbox = [cx - AOI_HALF_M, cy - AOI_HALF_M, cx + AOI_HALF_M, cy + AOI_HALF_M]
    cell = 2 * AOI_HALF_M / args.size
    params = {
        "bbox": ",".join(f"{v:.2f}" for v in bbox), "bboxSR": EPSG, "imageSR": EPSG,
        "size": f"{args.size},{args.size}", "format": "tiff", "pixelType": "F32",
        "compression": "None", "interpolation": "RSP_BilinearInterpolation",
        "noData": "-9999", "f": "image",
    }
    url = SERVICE + "/exportImage?" + urllib.parse.urlencode(params)
    raw = ROOT / "data" / "raw" / f"mt_st_helena_3dep_{cell:g}m.tif"
    if args.from_raw:
        buf = raw.read_bytes()
    else:
        # curl uses the OS trust store; python.org builds on macOS may lack CA certs.
        buf = subprocess.run(["curl", "-sSf", "--max-time", "180", url], check=True, capture_output=True).stdout
        if not buf.startswith((b"II", b"MM")):
            sys.exit("service did not return a TIFF: " + buf[:300].decode("utf-8", "replace"))
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(buf)
    sha = hashlib.sha256(buf).hexdigest()

    w, h, z = read_float_tiff(buf)
    nodata = sum(1 for v in z if v <= -9000 or v != v)
    valid = [v for v in z if v > -9000 and v == v]
    zmin, zmax = min(valid), max(valid)
    imax = max(range(len(z)), key=lambda i: z[i])

    # Block-mean downsample for the browser; record that resampling does not add accuracy.
    n = args.out_cells
    grid = []
    for gy in range(n):
        y0, y1 = gy * h // n, (gy + 1) * h // n
        for gx in range(n):
            x0, x1 = gx * w // n, (gx + 1) * w // n
            block = [z[y * w + x] for y in range(y0, y1) for x in range(x0, x1) if z[y * w + x] > -9000]
            grid.append(round(sum(block) / len(block)) if block else -32768)
    assets = ROOT / "prototype" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    binpath = assets / "terrain.bin"
    binpath.write_bytes(struct.pack("<" + "h" * len(grid), *grid))
    bin_sha = hashlib.sha256(binpath.read_bytes()).hexdigest()

    fetched = datetime.date.today().isoformat()
    source = {
        "source": "USGS 3D Elevation Program (3DEP) Bare Earth DEM dynamic service",
        "service": SERVICE, "request_url": url, "fetched": fetched,
        "rights": "USGS-produced data, public domain in the U.S.; credit: U.S. Geological Survey",
        "horizontal_crs": f"EPSG:{EPSG} (NAD83 / UTM zone 10N)",
        "vertical": "meters; service reports 3DEP bare-earth elevation (NAVD88 per 3DEP standard; not re-verified here)",
        "note": "Dynamic multi-resolution mosaic resampled by the service with bilinear interpolation; "
                "the underlying source dataset and survey epoch vary by location and are not recorded by this request.",
    }
    meta = {**source,
            "aoi": {"description": "~30 km square design extent centered on the GNIS feature point; not a geological boundary",
                    "center_gnis": {"feature_id": GNIS_ID, "lat": GNIS_LAT, "lon": GNIS_LON, "datum": "NAD83"},
                    "center_utm": [round(cx, 2), round(cy, 2)], "bbox_utm": [round(v, 2) for v in bbox]},
            "raw": {"file": str(raw.relative_to(ROOT)), "sha256": sha, "width": w, "height": h,
                    "cell_m": cell, "nodata_cells": nodata},
            "stats_raw_m": {"min": round(zmin, 2), "max": round(zmax, 2),
                            "max_cell_utm": [round(bbox[0] + (imax % w + .5) * cell, 1),
                                             round(bbox[3] - (imax // w + .5) * cell, 1)]},
            "browser_grid": {"file": "assets/terrain.bin", "sha256": bin_sha, "encoding": "int16 little-endian, meters, row 0 = north",
                             "cells": n, "cell_m": 2 * AOI_HALF_M / n, "resampling": "block mean from raw grid",
                             "nodata": -32768, "vertical_exaggeration_default": 1}}
    (assets / "terrain.json").write_text(json.dumps(meta, indent=2) + "\n")
    manifest_path = ROOT / "data" / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"datasets": []}
    manifest["datasets"] = [d for d in manifest["datasets"] if d.get("id") != "dem-3dep-aoi"]
    manifest["datasets"].append({"id": "dem-3dep-aoi", **source, "raw_file": meta["raw"]["file"],
                                 "raw_sha256": sha, "derived": [{"file": "prototype/assets/terrain.bin", "sha256": bin_sha}]})
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"raw {w}x{h} @ {cell:g} m, sha256 {sha[:16]}…, nodata {nodata}, "
          f"elev {zmin:.1f}–{zmax:.1f} m; browser grid {n}x{n} @ {2 * AOI_HALF_M / n:g} m")


if __name__ == "__main__":
    main()
