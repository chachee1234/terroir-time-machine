#!/usr/bin/env python3
"""Build terrain grids for a location outside the California UTM frames (stdlib only).

Reads data/locations/<id>.json. For each frame it samples AWS Open Data Terrain Tiles (Terrarium
PNGs, the same source and decoder as fetch_tiles.py, SOURCES.md G19) on a grid equally spaced in
longitude and latitude, with the row count chosen so cells are roughly square on the ground at the
frame's middle latitude. Land and sea floor come from the same mosaic (SRTM/GMTED on land, ETOPO1
and similar bathymetry offshore).

Writes <assets_dir>/<frame>.bin (Int16 little-endian metres, row 0 north) and <assets_dir>/terrain.json
(frames, shapes, bboxes, min/max, tile digests), and records the files in data/manifest.json.

  python3 scripts/build_location.py data/locations/gibraltar.json
  python3 scripts/build_location.py data/locations/gibraltar.json --offline   # cached tiles only
"""
import argparse
import datetime
import hashlib
import json
import math
import sys
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_tiles import RIGHTS, Mosaic, merc_px  # noqa: E402


def frame_shape(bbox, cols):
    lon0, lat0, lon1, lat1 = bbox
    kx = math.cos(math.radians((lat0 + lat1) / 2))
    rows = int(round(cols * (lat1 - lat0) / ((lon1 - lon0) * kx)))
    return cols, rows


def tiles_for_lonlat(bbox, z):
    lon0, lat0, lon1, lat1 = bbox
    x0, y0 = merc_px(lat1, lon0, z)
    x1, y1 = merc_px(lat0, lon1, z)
    n = 2 ** z
    return [(tx, ty) for tx in range(max(0, int(x0) // 256 - 1), min(n, int(x1) // 256 + 2))
            for ty in range(max(0, int(y0) // 256 - 1), min(n, int(y1) // 256 + 2))]


def sample_frame(mos, bbox, cols, rows):
    lon0, lat0, lon1, lat1 = bbox
    out = array("h")
    for r in range(rows):
        lat = lat1 - (r + 0.5) / rows * (lat1 - lat0)
        for c in range(cols):
            lon = lon0 + (c + 0.5) / cols * (lon1 - lon0)
            out.append(max(-32768, min(32767, int(round(mos.sample(lat, lon))))))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("location")
    ap.add_argument("--offline", action="store_true", help="use cached tiles only")
    args = ap.parse_args(argv)

    loc_path = Path(args.location)
    loc = json.loads(loc_path.read_text())
    out_dir = ROOT / loc["assets_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {"location": loc["id"], "name": loc["name"], "units": "m", "dtype": "int16le", "row0": "north",
            "grid": "equal steps in longitude and latitude, cell centres", "source": RIGHTS,
            "built": datetime.date.today().isoformat(), "frames": []}
    manifest_files = []
    for fr in loc["frames"]:
        bbox, z = fr["bbox_lonlat"], fr["zoom"]
        cols, rows = frame_shape(bbox, fr["cols"])
        mos = Mosaic(z, offline=args.offline)
        tiles = tiles_for_lonlat(bbox, z)
        mos.prefetch(tiles)
        grid = sample_frame(mos, bbox, cols, rows)
        if sys.byteorder != "little":
            grid.byteswap()
        path = out_dir / f"{fr['id']}.bin"
        path.write_bytes(grid.tobytes())
        cell_km = (bbox[2] - bbox[0]) / cols * 111.32 * math.cos(math.radians((bbox[1] + bbox[3]) / 2))
        meta["frames"].append({"id": fr["id"], "name": fr["name"], "file": path.name, "cols": cols, "rows": rows,
                               "bbox_lonlat": bbox, "cell_km": round(cell_km, 3), "zoom": z,
                               "tiles": len(tiles), "tile_digest": mos.digest(),
                               "min_m": min(grid), "max_m": max(grid),
                               "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        manifest_files.append(path)
        print(f"{fr['id']}: {cols} x {rows}, {cell_km:.2f} km cells, {len(tiles)} z{z} tiles, "
              f"{min(grid)} .. {max(grid)} m -> {path.relative_to(ROOT)}")
    tj = out_dir / "terrain.json"
    tj.write_text(json.dumps(meta, indent=1) + "\n")

    man_path = ROOT / "data" / "manifest.json"
    man = json.loads(man_path.read_text())
    entries = man.setdefault("locations", {})
    entries[loc["id"]] = {"location_file": str(loc_path.resolve().relative_to(ROOT)), "built": meta["built"],
                          "files": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in manifest_files + [tj]}}
    man_path.write_text(json.dumps(man, indent=2) + "\n")


if __name__ == "__main__":
    main()
