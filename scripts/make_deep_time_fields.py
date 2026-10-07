#!/usr/bin/env python3
"""Fields for the two deep-time animation pages.

  mayacamas  -> prototype/assets/regions/napa_valley/mayacamas_8ma.{u8,json}
                Napa-Sonoma frame (terrain.bin grid, 546 x 548, ~140 m): Sonoma Volcanics mask from the SIM 2956
                drape (units Ts*), a modelled eruption age per cell, and the frame's strike-slip faults in local km.
  westcoast  -> prototype/assets/plates/west_coast.{i16,json}
                lon -132..-112, lat 30..44 relief: the California grid (globe/california.bin, 0.02 deg) where it
                covers, the globe relief (globe/relief.png, ~0.088 deg) elsewhere; plus the San Andreas trace and
                the base-of-slope line used as the trench / transform in the animation.

Only files already in the repo are read. Everything here feeds a model animation: the eruption ages are a
north-younging ramp fitted to the published 8-2.5 Ma span (SOURCES G01), not dates per cell; the San Andreas
trace is a hand-simplified line through well-known points (good to ~10 km), not a mapped trace.
"""
import json, math, os, sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from make_geology_texture import utm_forward  # noqa: E402
from make_corison_100ka import box, smooth01  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
P = os.path.join(ROOT, "prototype/assets/")
WGS84 = (6378137.0, 1 / 298.257223563)

# Hand-simplified San Andreas Fault trace, north to south (lat, lon), with its continuation down the Gulf of
# California spreading axis. Points are well-known places on or next to the fault.
SAF = [(40.35, -124.55), (39.6, -124.05), (38.95, -123.73), (38.30, -123.05), (37.90, -122.68), (37.55, -122.45),
       (37.25, -122.15), (36.85, -121.54), (36.40, -120.95), (35.90, -120.43), (35.40, -119.90), (34.80, -118.90),
       (34.50, -118.20), (34.30, -117.45), (33.95, -116.80), (33.40, -115.90), (32.60, -115.30), (31.70, -114.65),
       (31.00, -114.00), (30.20, -113.30), (29.0, -112.6)]
# Pinnacles (west of the fault) and the Neenach volcanics (east): one 23 Ma volcanic field cut in two.
POINTS = {"Pinnacles": (36.48, -121.18), "Neenach": (34.77, -118.60), "Napa Valley": (38.40, -122.40),
          "Clear Lake volcanoes": (38.95, -122.75), "Cape Mendocino": (40.40, -124.40), "San Francisco": (37.77, -122.42),
          "Los Angeles": (34.05, -118.25)}

MAYA_PLACES = {"Corison": (38.484983, -122.44736), "Mt. St. Helena": (38.669, -122.633), "Napa": (38.297, -122.286),
               "Sonoma": (38.292, -122.458), "Mayacamas Mountains": (38.36, -122.56), "Santa Rosa": (38.44, -122.71),
               "Calistoga": (38.579, -122.580)}


def mayacamas():
    A = P + "regions/napa_valley/"
    tm = json.load(open(A + "terrain.json"))
    bg = tm["browser_grid"]
    W, H, cell = bg["cols"], bg["rows"], bg["cell_m"]
    x0, y0, x1, y1 = tm["aoi"]["bbox_utm"]
    legend = json.load(open(A + "geology_legend.json"))
    volc_cols = {u["color"].lower() for u in legend["units"] if u["ptype"].startswith("Ts")}
    g = np.array(Image.open(A + "geology.png").convert("RGBA"))
    assert g.shape[:2] == (H, W), g.shape
    hexes = np.vectorize(lambda r, gg, b: "#%02x%02x%02x" % (r, gg, b))(g[..., 0], g[..., 1], g[..., 2])
    volc = np.isin(hexes, list(volc_cols)).astype(np.float64) * (g[..., 3] > 0)
    volc_s = np.clip(box(volc, 3) * 1.4, 0, 1)
    # modelled eruption age, Ma: 8.0 at the south edge to 2.6 at the north edge, +-0.5 Ma of smooth noise
    rng = np.random.default_rng(7)
    noise = box(rng.standard_normal((H, W)), 8)
    noise = noise / (np.abs(noise).max() + 1e-9)
    north = 1 - (np.arange(H) + 0.5) / H
    te = 8.0 + (2.6 - 8.0) * north[:, None] + 0.5 * noise
    te = np.clip(te, 2.4, 8.0)

    gl = json.load(open(P + "geolibre/napa_valley.geolibre.json"))
    faults = []
    for lay in gl["layers"]:
        for f in (lay.get("geojson") or {}).get("features", []):
            pr = f["properties"]
            if f["geometry"]["type"] != "LineString" or pr.get("kind") != "strike-slip":
                continue
            rate = float("".join(ch for ch in pr["slip_rate"] if ch.isdigit() or ch == "."))
            pts = []
            for lo, la in f["geometry"]["coordinates"]:
                e, n = utm_forward(math.radians(la), math.radians(lo), WGS84)
                pts.append([round((e - x0) / 1000, 3), round((n - y0) / 1000, 3)])
            if any(-5 < x < (x1 - x0) / 1000 + 5 and -5 < y < (y1 - y0) / 1000 + 5 for x, y in pts):
                faults.append({"name": pr["name"], "mm_yr": rate, "km": pts})

    places = {}
    for name, (la, lo) in MAYA_PLACES.items():
        e, n = utm_forward(math.radians(la), math.radians(lo), WGS84)
        places[name] = [round((e - x0) / 1000, 3), round((n - y0) / 1000, 3)]
    out = np.stack([np.round(volc_s * 255), np.round(te * 30)]).astype(np.uint8)
    out.tofile(A + "mayacamas_8ma.u8")
    json.dump({"built_by": "scripts/make_deep_time_fields.py", "grid": {"cols": W, "rows": H, "cell_m": cell,
               "bbox_utm": [x0, y0, x1, y1], "row0": "north"},
               "fields": ["volcanic", "erupt_ma"], "scale": {"volcanic": 1 / 255, "erupt_ma": 1 / 30},
               "volcanic_units": sorted(u["ptype"] for u in legend["units"] if u["ptype"].startswith("Ts")),
               "erupt_ma_status": "modelled: north-younging ramp across the published ~8-2.5 Ma span, not per-cell dates",
               "places_km": places, "faults": faults}, open(A + "mayacamas_8ma.json", "w"), indent=1)
    print("mayacamas", out.shape, "volcanic cells", int(volc.sum()), "faults", [f["name"] for f in faults])


def westcoast():
    LON0, LON1, LAT0, LAT1, D = -132.0, -112.0, 30.0, 44.0, 0.035
    W, H = int(round((LON1 - LON0) / D)) + 1, int(round((LAT1 - LAT0) / D)) + 1
    lon = LON0 + np.arange(W) * D
    lat = LAT1 - np.arange(H) * D
    LO, LA = np.meshgrid(lon, lat)
    # globe relief (8-bit, equirectangular)
    rl = json.load(open(P + "globe/relief.json"))
    v = np.array(Image.open(P + "globe/relief.png").convert("L")).astype(np.float64)
    rw, rh = rl["width"], rl["height"]

    def relief_at(lo, la):
        fx = (lo + 180) / 360 * rw - 0.5
        fy = (90 - la) / 180 * rh - 0.5
        x0_, y0_ = np.floor(fx).astype(int), np.floor(fy).astype(int)
        tx, ty = fx - x0_, fy - y0_
        g = lambda yy, xx: v[np.clip(yy, 0, rh - 1), np.clip(xx, 0, rw - 1)]
        val = (g(y0_, x0_) * (1 - tx) + g(y0_, x0_ + 1) * tx) * (1 - ty) + (g(y0_ + 1, x0_) * (1 - tx) + g(y0_ + 1, x0_ + 1) * tx) * ty
        return np.where(val >= 128, ((val - 128) / 127) ** 2 * 8848, -((127 - val) / 127) ** 2 * 11000)

    z = relief_at(LO, LA)
    cm = json.load(open(P + "globe/california.json"))
    c = np.fromfile(P + "globe/california.bin", "<i2").reshape(cm["rows"], cm["cols"]).astype(np.float64)
    b = cm["box_lonlat"]
    inside = (LO >= b[0]) & (LO <= b[2]) & (LA >= b[1]) & (LA <= b[3])
    fx = (LO - b[0]) / cm["cell_deg"]
    fy = (b[3] - LA) / cm["cell_deg"]
    ci = np.clip(np.round(fx).astype(int), 0, cm["cols"] - 1)
    ri = np.clip(np.round(fy).astype(int), 0, cm["rows"] - 1)
    cz = c[ri, ci]
    # feather the seam over ~0.3 deg
    edge = np.minimum.reduce([LO - b[0], b[2] - LO, LA - b[1], b[3] - LA])
    w = np.clip(edge / 0.3, 0, 1) * inside
    z = z * (1 - w) + cz * w

    # base of the continental slope: per row, scanning west from the coast, first cell deeper than 2,600 m
    trench = []
    for r in range(H):
        row = z[r]
        land = np.where((row > 0) & (lon < -114))[0]
        if not len(land):
            continue
        cw = land.min()
        deep = np.where(row[:cw] < -2600)[0]
        if len(deep):
            trench.append([round(float(lat[r]), 3), round(float(lon[deep.max()]), 3)])
    # smooth the line along latitude
    tl = np.array(trench)
    k = 9
    sm = np.convolve(np.pad(tl[:, 1], k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="valid")
    trench = [[float(a), round(float(o), 3)] for a, o in zip(tl[:, 0], sm)][::4]

    np.clip(np.round(z), -32000, 32000).astype("<i2").tofile(P + "plates/west_coast.i16")
    json.dump({"built_by": "scripts/make_deep_time_fields.py", "lon": [LON0, LON1], "lat": [LAT0, LAT1], "cell_deg": D,
               "cols": W, "rows": H, "encoding": "Int16 little-endian metres, row 0 = north",
               "sources": "globe/california.bin (Terrain Tiles z8) inside its box, globe/relief.png outside (SOURCES G19)",
               "saf": SAF, "saf_status": "hand-simplified through well-known places, ~10 km; Gulf of California axis south of 32.6 N",
               "trench": trench, "trench_status": "base of today's continental slope (-2,600 m), smoothed; stands in for the old trench",
               "points": POINTS}, open(P + "plates/west_coast.json", "w"), indent=1)
    print("westcoast", (H, W), "z range", round(float(z.min())), round(float(z.max())), "trench pts", len(trench))


if __name__ == "__main__":
    mayacamas()
    westcoast()
