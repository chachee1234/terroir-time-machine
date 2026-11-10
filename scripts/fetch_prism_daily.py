#!/usr/bin/env python3
"""Daily weather for a region frame from PRISM (4 km daily, 1981 to recent days, Oregon State University).

Tier 0, standard library only. PRISM serves each day and variable as one GeoTIFF for the lower 48 states
(about 1-2.5 MB zipped; services.nacse.org/prism/data/get/us/4km/<var>/<YYYYMMDD>). Each file is downloaded
into memory, clipped to the frame with make_climate's TIFF reader, and only the clipped cells are cached in
data/raw/prism_daily/<region>/<var>/<YYYYMMDD>.f32 (git-ignored), so a long run can stop and resume.

Variables: tmax (daily maximum temperature, C), tmin (daily minimum, C), ppt (precipitation, mm).

Output, written by --pack (or after fetching): <assets_dir>/daily/
  index.json   grid, variables, scale, list of years with their first day and day count, source, rights
  <year>.bin   int16 little-endian, [variable][day of year][cell], cells row-major, north row first,
               value = round(x * 10), -32768 = no data (outside PRISM, or a day not fetched)

Rights: PRISM Climate Group, Oregon State University, https://prism.oregonstate.edu. Free to use with that
credit (PRISM terms of use). Daily data approved by the owner 2026-10-08. SOURCES.md G41.

Usage: fetch_prism_daily.py --region data/regions/napa_valley.json [--start 1981-01-01] [--end YYYY-MM-DD]
                            [--workers 4] [--pack]
"""
import argparse
import datetime
import io
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from array import array
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_climate import Tiff, frame_window, clip  # noqa: E402
from fetch_tiles import geographic_from_utm  # noqa: E402
from net import open_url  # noqa: E402

URL = "https://services.nacse.org/prism/data/get/us/4km/{var}/{day}"
VARS = ("tmax", "tmin", "ppt")
NODATA = -32768
FIRST = datetime.date(1981, 1, 1)
SOURCE = ("PRISM Climate Group, Oregon State University, AN81d 4 km daily time series "
          "(https://prism.oregonstate.edu)")
RIGHTS = "Free to use with credit to the PRISM Climate Group, Oregon State University (PRISM terms of use)."


def cache_dir(region):
    return ROOT / "data" / "raw" / "prism_daily" / region["id"]


def download(var, day, tries=4):
    url = URL.format(var=var, day=day.strftime("%Y%m%d"))
    req = urllib.request.Request(url, headers={"User-Agent": "terroir-time-machine"})
    for k in range(tries):
        try:
            with open_url(req, timeout=120) as r:
                data = r.read()
            if data.startswith(b"PK"):
                return data
            err = data[:200]
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            err = e
        time.sleep(2 ** (k + 1))
    raise RuntimeError(f"{url}: {err!r}")


def read_tif(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return Tiff(z.read(next(n for n in z.namelist() if n.endswith(".tif"))))


def grid_for(region, tif):
    r0, c0, rows, cols = frame_window(region, tif)
    return (r0, c0, rows, cols), {
        "lon0": round(tif.lon0 + c0 * tif.dlon, 6), "lat0": round(tif.lat0 - r0 * tif.dlat, 6),
        "dlon": tif.dlon, "dlat": tif.dlat, "cols": cols, "rows": rows,
        "note": "lon0/lat0 is the north-west corner of the north-west cell; NAD83 geographic"}


def fetch_one(region, win, var, day):
    path = cache_dir(region) / var / f"{day:%Y%m%d}.f32"
    if path.exists():
        return "cached"
    vals = clip(read_tif(download(var, day)), win)
    a = array("f", [float("nan") if v is None else v for v in vals])
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(a.tobytes())
    tmp.replace(path)
    return "fetched"


def setup(region):
    """Window and grid from one reference file, cached in grid.json so every day uses the same cells."""
    gpath = cache_dir(region) / "grid.json"
    if gpath.exists():
        g = json.loads(gpath.read_text())
        return tuple(g["window"]), g["grid"]
    win, grid = grid_for(region, read_tif(download("tmax", FIRST)))
    gpath.parent.mkdir(parents=True, exist_ok=True)
    gpath.write_text(json.dumps({"window": win, "grid": grid}))
    return win, grid


def fetch_range(region, start, end, workers):
    win, _ = setup(region)
    jobs = [(v, start + datetime.timedelta(d)) for d in range((end - start).days + 1) for v in VARS]
    done, failed, t0 = 0, [], time.time()
    with ProcessPoolExecutor(workers) as ex:
        futs = {ex.submit(fetch_one, region, win, v, d): (v, d) for v, d in jobs}
        for f in futs:
            v, d = futs[f]
            try:
                f.result()
            except Exception as e:  # keep going; a missing day is packed as no data
                failed.append(f"{v} {d}: {e}")
            done += 1
            if done % 300 == 0:
                print(f"{done}/{len(jobs)} files, {time.time() - t0:.0f} s", file=sys.stderr, flush=True)
    for line in failed:
        print("failed:", line, file=sys.stderr)
    return failed


def texture_map(region, grid, texel_m=1000):
    """For a texel_m grid over the region's UTM frame (row 0 north), the PRISM cell index under each texel
    centre, or -1 outside the grid. The viewer paints each day's cell values through this map."""
    x0, y0, x1, y1 = region["bbox_utm"]
    cols, rows = max(1, round((x1 - x0) / texel_m)), max(1, round((y1 - y0) / texel_m))
    cells = []
    for r in range(rows):
        n = y1 - (r + 0.5) * (y1 - y0) / rows
        for c in range(cols):
            lat, lon = geographic_from_utm(x0 + (c + 0.5) * (x1 - x0) / cols, n, region.get("utm_zone", 10))
            gc = int((lon - grid["lon0"]) / grid["dlon"])
            gr = int((grid["lat0"] - lat) / grid["dlat"])
            cells.append(gr * grid["cols"] + gc if 0 <= gr < grid["rows"] and 0 <= gc < grid["cols"] else -1)
    return {"bbox_utm": [x0, y0, x1, y1], "cols": cols, "rows": rows, "cell": cells,
            "note": "PRISM cell index under each texel centre, row-major, north row first; -1 outside"}


def pack(region):
    """Write <assets_dir>/daily/<year>.bin and index.json from the cached days."""
    win, grid = setup(region)
    ncell = grid["rows"] * grid["cols"]
    out = ROOT / region["assets_dir"] / "daily"
    out.mkdir(parents=True, exist_ok=True)
    years, last_day = [], None
    cache = cache_dir(region)
    found = sorted(p.stem for p in (cache / "tmax").glob("*.f32"))
    if not found:
        raise SystemExit("nothing cached yet")
    y0, y1 = int(found[0][:4]), int(found[-1][:4])
    for year in range(y0, y1 + 1):
        first = datetime.date(year, 1, 1)
        ndays = (datetime.date(year + 1, 1, 1) - first).days
        buf = array("h", [NODATA]) * (len(VARS) * ndays * ncell)
        have = 0
        for vi, var in enumerate(VARS):
            for d in range(ndays):
                p = cache / var / f"{first + datetime.timedelta(d):%Y%m%d}.f32"
                if not p.exists():
                    continue
                a = array("f")
                a.frombytes(p.read_bytes())
                base = (vi * ndays + d) * ncell
                for i, v in enumerate(a):
                    if v == v:
                        buf[base + i] = max(-32767, min(32767, round(v * 10)))
                if vi == 0:
                    have += 1
                    last_day = max(last_day or first, first + datetime.timedelta(d))
        if sys.byteorder == "big":
            buf.byteswap()
        (out / f"{year}.bin").write_bytes(buf.tobytes())
        years.append({"year": year, "days": ndays, "days_with_data": have})
    index = {"source": SOURCE, "rights": RIGHTS, "built": datetime.date.today().isoformat(), "grid": grid,
             "vars": list(VARS), "units": {"tmax": "C", "tmin": "C", "ppt": "mm"}, "scale": 0.1,
             "nodata": NODATA, "layout": "int16 LE [var][day of year][cell], cells row-major, north row first",
             "years": years, "last_day": last_day.isoformat(), "texture": texture_map(region, grid),
             "limits": "4 km cells: one value per cell, so a hillside and the valley floor beside it share a "
                       "value. PRISM interpolates station readings; recent months are provisional and may be "
                       "revised by PRISM."}
    (out / "index.json").write_text(json.dumps(index, indent=1) + "\n")
    mark_layer(region["id"])
    return index, out


def mark_layer(region_id, layer="daily"):
    """List `layer` for the region in prototype/assets/regions/index.json. The viewer only asks for the daily
    files when it is listed, so a site built without them shows no Weather chip and logs no 404."""
    p = ROOT / "prototype" / "assets" / "regions" / "index.json"
    if not p.exists():
        return False
    idx = json.loads(p.read_text())
    for r in idx["regions"]:
        if r["id"] == region_id and layer not in r.setdefault("layers", []):
            r["layers"].append(layer)
            p.write_text(json.dumps(idx, indent=1) + "\n")
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--start", default=FIRST.isoformat())
    ap.add_argument("--end", default=(datetime.date.today() - datetime.timedelta(2)).isoformat())
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--pack", action="store_true", help="only pack what is cached, no downloads")
    a = ap.parse_args()
    region = json.loads(Path(a.region).read_text())
    if not a.pack:
        fetch_range(region, datetime.date.fromisoformat(a.start), datetime.date.fromisoformat(a.end), a.workers)
    index, out = pack(region)
    print(f"{out.relative_to(ROOT)}: {len(index['years'])} years, last day {index['last_day']}, "
          f"{index['grid']['cols']} x {index['grid']['rows']} cells")


if __name__ == "__main__":
    main()
