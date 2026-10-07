#!/usr/bin/env python3
"""Fields for the Corison 100,000-year animation (prototype/corison-100ka.html).

Reads only files already in the repo: the site's 10 m close-up (detail/corison.*), the SIM 2956 unit colours
(geology_legend.json), today's NHD channels (rivers.json), the CDL 2024 grape drape (vineyards.png) and the
UCERF3 West Napa Fault trace (assets/geolibre/napa_valley.geolibre.json).

Writes prototype/assets/regions/napa_valley/sites/corison_100ka.u8 (uint8 fields, 501 x 501, row 0 = north)
and corison_100ka.json (field list, scales, the fault in local metres, the illustrated old channel).

What is measured and what is modelled:
  measured  - today's ground, which map unit is where (and so which surfaces are Holocene), today's channels,
              grape blocks in 2024, the fault trace and its slip rate.
  modelled  - every thickness written here. The map says a Holocene unit was laid down in the last ~11,700 years;
              how thick it is under Corison is not measured, so the thicknesses below are round illustrative
              numbers, tapered to zero at the hill front so the old ground meets the hills without a step.
"""
import json, math, os, sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from make_geology_texture import utm_forward  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
A = os.path.join(ROOT, "prototype/assets/regions/napa_valley/")
WGS84 = (6378137.0, 1 / 298.257223563)

# SIM 2956 units on the valley floor in this frame. Prefix Qh = Holocene; Qf = fan deposits mapped as
# Holocene and late Pleistocene; Qpf = Pleistocene fan; Qa = alluvium. Everything else here is hill rock or landslide.
HOLOCENE = {"Qhf", "Qhff", "Qht", "Qhty", "Qhay", "Qhc", "Qha", "af", "alf", "water"}
LATE_FAN = {"Qf", "Qa"}
OLD_FAN = {"Qpf"}

# Illustrative thicknesses (m). Not measured: see the module docstring.
T_PLEIST = 8.0    # fill laid down 71-14 ka under every young unit
T_FAN = 3.0       # extra late fan building, 14-6 ka, under Qf / Qa
T_HOLO = 5.0      # Holocene fill, 11.7-0.2 ka, under Qh units
INCISE = 6.0      # extra depth the Napa River cuts at the last glacial maximum
SCALE = 20.0      # uint8 = metres x 20 (0.05 m steps, up to 12.75 m)


def box(a, r):
    """Separable box blur, radius r cells, edge-padded; three passes approximate a gaussian."""
    for _ in range(3):
        for ax in (0, 1):
            p = np.pad(a, [(r, r) if i == ax else (0, 0) for i in range(2)], mode="edge")
            c = np.cumsum(p, axis=ax, dtype=np.float64)
            c = np.concatenate([np.zeros_like(c.take([0], axis=ax)), c], axis=ax)
            n = a.shape[ax]
            a = (c.take(range(2 * r + 1, n + 2 * r + 1), axis=ax) - c.take(range(0, n), axis=ax)) / (2 * r + 1)
    return a


def smooth01(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def draw_lines(shape, lines, px, width_cells):
    """Rasterise polylines (lists of (e, n)) to a 0/1 mask with a round brush."""
    h, w = shape
    m = np.zeros(shape, np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    for pts, wc in zip(lines, width_cells):
        for (e0, n0), (e1, n1) in zip(pts, pts[1:]):
            c0, r0 = px(e0, n0); c1, r1 = px(e1, n1)
            steps = int(max(abs(c1 - c0), abs(r1 - r0)) * 2) + 1
            for s in range(steps + 1):
                c = c0 + (c1 - c0) * s / steps; r = r0 + (r1 - r0) * s / steps
                if -wc <= c < w + wc and -wc <= r < h + wc:
                    lo_r, hi_r = int(max(0, r - wc - 1)), int(min(h, r + wc + 2))
                    lo_c, hi_c = int(max(0, c - wc - 1)), int(min(w, c + wc + 2))
                    sub = (yy[lo_r:hi_r, lo_c:hi_c] - r) ** 2 + (xx[lo_r:hi_r, lo_c:hi_c] - c) ** 2 <= wc * wc
                    m[lo_r:hi_r, lo_c:hi_c][sub] = 1
    return m


def main():
    meta = json.load(open(A + "detail/corison.json"))
    x0, y0, x1, y1 = meta["bbox_utm"]
    W, H = meta["cols"], meta["rows"]
    cell = meta["cell_m"]
    px = lambda e, n: ((e - x0) / cell - 0.5, (y1 - n) / cell - 0.5)   # cell centres

    # ---- map units -> young-deposit classes
    legend = json.load(open(A + "geology_legend.json"))
    by_color = {u["color"].lower(): u["ptype"] for u in legend["units"]}
    g = np.array(Image.open(A + "detail/corison.geology.png").convert("RGBA"))
    hexes = np.vectorize(lambda r, gg, b: "#%02x%02x%02x" % (r, gg, b))(g[..., 0], g[..., 1], g[..., 2])
    unit = np.vectorize(lambda h: by_color.get(h, ""))(hexes)
    holo = np.isin(unit, list(HOLOCENE)).astype(np.float64)
    late = np.isin(unit, list(LATE_FAN)).astype(np.float64)
    oldf = np.isin(unit, list(OLD_FAN)).astype(np.float64)
    young = np.clip(holo + late + oldf, 0, 1)

    # taper: full thickness only well inside the valley floor (~250 m from the hill front)
    inside = smooth01(box(young, 12), 0.5, 0.97) * young
    inside = box(inside, 3)

    def field(mask, t):
        return np.clip(box(mask, 4) * inside * t, 0, 255 / SCALE)

    pleist = field(np.clip(young - oldf, 0, 1), T_PLEIST) + field(oldf, T_PLEIST * 0.6)
    fan = field(late, T_FAN)
    hol = field(holo, T_HOLO)

    # ---- today's channels
    rv = json.load(open(A + "rivers.json"))
    lines, names, sizes = [], [], []
    for L in rv["lines"]:
        xs, ys = [L[3]], [L[4]]
        for i in range(5, len(L), 2):
            xs.append(xs[-1] + L[i]); ys.append(ys[-1] + L[i + 1])
        pts = list(zip(xs, ys))
        if any(x0 - 200 <= e <= x1 + 200 and y0 - 200 <= n <= y1 + 200 for e, n in pts):
            lines.append(pts); names.append(rv["names"][L[0]] if L[0] >= 0 else ""); sizes.append(L[1])
    napa = [p for p, nm in zip(lines, names) if nm == "Napa River"]
    river = draw_lines((H, W), napa, px, [2.2] * len(napa))
    creeks = draw_lines((H, W), [p for p, nm in zip(lines, names) if nm != "Napa River"], px,
                        [0.8 + 0.35 * s for s, nm in zip(sizes, names) if nm != "Napa River"])
    incise = np.clip(box(river, 6) * 4.5, 0, 1) * young     # LGM trench, ~150 m wide, valley floor only

    # ---- illustrated old channel across the property (owner recollection S0: "an ancient river crossing the
    # property"; the Bale profile's deepest layers are rounded stream gravel, S4). Route: from where the creek
    # south of the site leaves the hills, through the site, to the Napa River. Not mapped.
    ce, cn = meta["bbox_utm"][0] + 2500, meta["bbox_utm"][1] + 2500
    route = [(ce - 1080, cn - 280), (ce - 640, cn - 170), (ce - 260, cn - 30), (ce, cn + 10),
             (ce + 380, cn + 60), (ce + 820, cn + 190), (ce + 1250, cn + 330), (ce + 1730, cn + 560)]

    # ---- grapes 2024 (CDL), resampled from the 30 m frame grid
    vm = json.load(open(A + "vineyards.json"))["drape"]
    vx0, vy0, vx1, vy1 = vm["bbox_utm"]
    v = np.array(Image.open(A + "vineyards.png"))
    vh, vw = v.shape
    ee = x0 + (np.arange(W) + 0.5) * cell; nn = y1 - (np.arange(H) + 0.5) * cell
    ci = np.clip(((ee - vx0) / (vx1 - vx0) * vw).astype(int), 0, vw - 1)
    ri = np.clip(((vy1 - nn) / (vy1 - vy0) * vh).astype(int), 0, vh - 1)
    vines = v[np.ix_(ri, ci)].astype(np.float64)

    # ---- West Napa Fault (UCERF3 trace via GEM GAF-DB), to local metres from the frame's SW corner
    gl = json.load(open(os.path.join(ROOT, "prototype/assets/geolibre/napa_valley.geolibre.json")))
    trace = None
    for lay in gl["layers"]:
        for f in (lay.get("geojson") or {}).get("features", []):
            if f["properties"].get("name") == "West Napa Fault":
                trace, slip = f["geometry"]["coordinates"], f["properties"]["slip_rate"]
    fault = [utm_forward(math.radians(la), math.radians(lo), WGS84) for lo, la in trace]

    fields = {"pleist": pleist * SCALE, "fan": fan * SCALE, "hol": hol * SCALE, "incise": incise * 255,
              "creeks": box(creeks, 1) * 255, "vines": vines * 255, "young": inside * 255}
    order = list(fields)
    out = np.stack([np.clip(np.round(fields[k]), 0, 255).astype(np.uint8) for k in order])
    out.tofile(A + "sites/corison_100ka.u8")
    loc = lambda e, n: [round(e - x0, 1), round(n - y0, 1)]
    js = {
        "built_by": "scripts/make_corison_100ka.py",
        "grid": {"cols": W, "rows": H, "cell_m": cell, "bbox_utm": meta["bbox_utm"], "row0": "north"},
        "fields": order,
        "scale": {"pleist": 1 / SCALE, "fan": 1 / SCALE, "hol": 1 / SCALE, "incise": 1 / 255, "creeks": 1 / 255,
                  "vines": 1 / 255, "young": 1 / 255},
        "thickness_m": {"pleistocene_fill": T_PLEIST, "late_fan": T_FAN, "holocene": T_HOLO, "lgm_incision": INCISE,
                        "status": "illustrative, not measured"},
        "site_local_m": loc(*json.load(open(A + "sites/corison.json"))["location"]["utm"]),
        "fault": {"name": "West Napa Fault", "slip_rate": slip, "source": "USGS UCERF3 via GEM GAF-DB",
                  "local_m": [loc(e, n) for e, n in fault]},
        "old_channel_local_m": [loc(e, n) for e, n in route],
        "napa_river_local_m": [[loc(e, n) for e, n in p] for p in napa],
    }
    json.dump(js, open(A + "sites/corison_100ka.json", "w"), indent=1)
    print("wrote", out.shape, {k: round(float(fields[k].max()), 1) for k in order})


if __name__ == "__main__":
    main()
