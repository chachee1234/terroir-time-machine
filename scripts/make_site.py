#!/usr/bin/env python3
"""One vineyard site in detail: the evidence file data/sites/<id>.json turned into what the viewer draws.

Tier 0, standard library only. Reads the site's evidence (location, reported soil series, claims with sources),
then adds, each from its own source:
  soil     the soil series' horizons (depths, texture, Munsell colours, pH, rock fragments) from the USDA
           Official Series Description, via the SoilKnowledgeBase JSON snapshot on GitHub (cached in
           data/raw/osd/, git-ignored). Colours are approximate sRGB from the Munsell notation (munsell_rgb).
  geology  the SIM 2956 unit at the site and along a SW-NE line across the valley through it (needs the
           owner-supplied eswn-geol.e00, as make_geology_texture.py does)
  profile  ground elevation along that line from the site's close-up terrain grid (fetch_tiles.py --only <id>)
  streams  where USGS NHD channels (rivers.json, make_rivers.py) cross the line
  ava      which AVA polygons (UC Davis AVA Project) contain the site
Output: <assets_dir>/sites/<id>.json and <assets_dir>/sites/index.json.

Nothing here is an animation: the viewer animates the layers in the order they were laid down, and labels
that order as an illustration. The horizons are the series' typical pedon, not a pit dug at this site.

Usage: make_site.py data/sites/corison.json --e00 data/raw/eswn-geol.e00 [--half 1900] [--step 10] [--offline]
"""
import argparse
import json
import math
import re
import sys
import urllib.request
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_terrain import utm_from_geographic  # noqa: E402
import make_geology_texture as mg  # noqa: E402

OSD_URL = "https://raw.githubusercontent.com/ncss-tech/SoilKnowledgeBase/main/inst/extdata/OSD/{c}/{s}.json"
OSD_CACHE = ROOT / "data" / "raw" / "osd"
AZ = math.radians(50.0)          # the viewer's section bearing: SW (left) to NE (right), across the valley
UX, UY = math.sin(AZ), math.cos(AZ)
HUE_DEG = {"5R": 25, "10R": 35, "2.5YR": 45, "5YR": 55, "7.5YR": 65, "10YR": 75, "2.5Y": 85, "5Y": 95}


def munsell_rgb(hue, value, chroma):
    """Approximate sRGB hex for a Munsell colour: value ~ L*/10, chroma ~ C*ab/5, hue on a CIELAB angle.
    Good enough to tell a dark topsoil from a pale gravel in a drawing; not a colorimetric conversion."""
    try:
        L, C = float(value) * 10.0, float(chroma) * 5.0
    except (TypeError, ValueError):
        return None
    h = math.radians(HUE_DEG.get(str(hue).upper(), 75))
    a, b = C * math.cos(h), C * math.sin(h)
    fy = (L + 16) / 116
    fx, fz = fy + a / 500, fy - b / 200
    inv = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    X, Y, Z = 0.95047 * inv(fx), inv(fy), 1.08883 * inv(fz)
    rgb = (3.2406 * X - 1.5372 * Y - 0.4986 * Z, -0.9689 * X + 1.8758 * Y + 0.0415 * Z, 0.0557 * X - 0.2040 * Y + 1.0570 * Z)
    g = lambda c: 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return "#" + "".join(f"{round(max(0, min(1, g(c))) * 255):02x}" for c in rgb)


def osd(series, offline=False):
    """The SoilKnowledgeBase JSON for one series (cached)."""
    s = series.upper()
    path = OSD_CACHE / f"{s}.json"
    if not path.exists():
        if offline:
            raise SystemExit(f"{path} missing (offline)")
        OSD_CACHE.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(OSD_URL.format(c=s[0], s=s), timeout=60) as r:
            path.write_bytes(r.read())
    return json.loads(path.read_text()), OSD_URL.format(c=s[0], s=s)


def gravel_pct(narrative):
    """Rock fragment percent stated in a horizon narrative ('about 20 percent fine gravel'), else None."""
    m = re.search(r"(\d+)\s*percent\s+(?:fine\s+|coarse\s+)?(?:gravel|pebbles|rock fragments)", narrative or "")
    return int(m.group(1)) if m else None


def horizons(doc):
    rows = []
    for h in (doc.get("HORIZONS") or [[]])[0]:
        nar = h.get("narrative") or ""
        tex = h.get("texture_class") or ""
        m = re.search(r"\)\s*((?:very |extremely )?(?:gravelly |cobbly |stony )?[a-z ]*?(?:loam|sand|clay|silt))\b", nar)
        if m:
            tex = m.group(1).strip()           # keep the modifier ("gravelly sandy loam") the texture class drops
        rows.append({"name": h["name"], "top_cm": h["top"], "bottom_cm": h["bottom"], "texture": tex,
                     "dry": f"{h.get('dry_hue')} {h.get('dry_value')}/{h.get('dry_chroma')}",
                     "moist": f"{h.get('moist_hue')} {h.get('moist_value')}/{h.get('moist_chroma')}",
                     "rgb": munsell_rgb(h.get("moist_hue"), h.get("moist_value"), h.get("moist_chroma")),
                     "rgb_dry": munsell_rgb(h.get("dry_hue"), h.get("dry_value"), h.get("dry_chroma")),
                     "pH": h.get("pH") if isinstance(h.get("pH"), (int, float)) else None,
                     "gravel_pct": gravel_pct(nar), "buried": h["name"].endswith("b"),
                     "structure": h.get("structure") if h.get("structure") not in (None, "NA") else None,
                     "narrative": nar})
    return rows


def section(doc, key):
    v = doc.get(key)
    if isinstance(v, dict):
        v = v.get("content")
    return re.sub(r"^[A-Z ]+:\s*", "", v or "").strip() or None


def load_grid(meta_path):
    meta = json.loads(meta_path.read_text())
    h = array("h")
    h.frombytes(meta_path.with_suffix(".bin").read_bytes())
    return meta, h


def elev(meta, h, e, n):
    """Bilinear elevation (m) on a fetch_tiles grid (points from bbox corner to corner, row 0 north)."""
    x0, y0, x1, y1 = meta["bbox_utm"]
    cols, rows = meta["cols"], meta["rows"]
    fx = (e - x0) / (x1 - x0) * (cols - 1)
    fy = (y1 - n) / (y1 - y0) * (rows - 1)
    if not (0 <= fx <= cols - 1 and 0 <= fy <= rows - 1):
        return None
    c, r = min(cols - 2, int(fx)), min(rows - 2, int(fy))
    u, v = fx - c, fy - r
    g = lambda rr, cc: h[rr * cols + cc] * meta.get("scale", 0.1)
    return (g(r, c) * (1 - u) + g(r, c + 1) * u) * (1 - v) + (g(r + 1, c) * (1 - u) + g(r + 1, c + 1) * u) * v


def point_in_rings(x, y, rings):
    inside = False
    for ring in rings:
        for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
            if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
                inside = not inside
    return inside


def avas_at(lat, lon, boundary):
    out = []
    for f in json.loads(boundary.read_text())["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        if any(point_in_rings(lon, lat, poly) for poly in polys):
            out.append({"id": f["properties"]["ava_id"], "name": f["properties"]["name"].strip()})
    return out


def stream_crossings(rivers, e0, n0, half):
    """Offsets (m, SW negative) where mapped channels cross the section line."""
    out = []
    ax, ay, bx, by = e0 - UX * half, n0 - UY * half, e0 + UX * half, n0 + UY * half
    for row in rivers["lines"]:
        ni, sc, per = row[0], row[1], row[2]
        x, y, pts = row[3], row[4], [(row[3], row[4])]
        for k in range(5, len(row), 2):
            x, y = x + row[k], y + row[k + 1]
            pts.append((x, y))
        for (px, py), (qx, qy) in zip(pts, pts[1:]):
            d1x, d1y, d2x, d2y = bx - ax, by - ay, qx - px, qy - py
            den = d1x * d2y - d1y * d2x
            if abs(den) < 1e-9:
                continue
            t = ((px - ax) * d2y - (py - ay) * d2x) / den
            s = ((px - ax) * d1y - (py - ay) * d1x) / den
            if 0 <= t <= 1 and 0 <= s <= 1:
                out.append({"offset_m": round(-half + 2 * half * t), "name": rivers["names"][ni] if ni >= 0 else None,
                            "size_class": sc, "perennial": bool(per)})
    out.sort(key=lambda c: c["offset_m"])
    return out


def build(site_path, e00, half=1900.0, step=10.0, offline=False):
    site = json.loads(Path(site_path).read_text())
    region = json.loads((ROOT / "data" / "regions" / f"{site['region']}.json").read_text())
    assets = ROOT / region["assets_dir"]
    lat, lon = site["location"]["lat"], site["location"]["lon"]
    e0, n0 = utm_from_geographic(lat, lon)

    doc, url = osd(site["soil"]["series"], offline)
    soil = dict(site["soil"], series_name=doc.get("SERIES"), osd_url=url, osd_revised=doc.get("REVDATE"),
                taxonomic_class=section(doc, "TAXONOMIC CLASS"), overview=section(doc, "OVERVIEW"),
                setting=section(doc, "GEOGRAPHIC SETTING"), drainage=section(doc, "DRAINAGE AND PERMEABILITY"),
                range=section(doc, "RANGE IN CHARACTERISTICS"), use=section(doc, "USE AND VEGETATION"),
                type_location=section(doc, "TYPE LOCATION"), horizons=horizons(doc))

    meta, h = load_grid(assets / "detail" / f"{site['id']}.json")
    n = int(round(2 * half / step)) + 1
    offs = [-half + 2 * half * i / (n - 1) for i in range(n)]
    pts = [(e0 + UX * o, n0 + UY * o) for o in offs]
    ground = [elev(meta, h, e, nn) for e, nn in pts]
    if any(g is None for g in ground):
        raise SystemExit("section line leaves the close-up grid: lower --half or enlarge the close-up")

    arcs, pat = mg.read_e00(e00)
    cell = step                                      # one local raster around the line, then nearest-cell lookups
    x0g, y1g = e0 - half - cell, n0 + half + cell
    cols = rows = int(2 * (half + cell) / cell) + 1
    de, dn = mg.nad83_to_nad27_offset(e0, n0)
    grid = mg.rasterize(arcs, x0g + de, y1g + dn, cell, cols, rows)
    unit = lambda e, nn: (lambda p: pat[p - 1]["PTYPE"] if 1 < p <= len(pat) else "")(
        grid[min(rows - 1, max(0, int((y1g - nn) / cell)))][min(cols - 1, max(0, int((e - x0g) / cell)))])
    runs = []
    for o, (e, nn) in zip(offs, pts):
        u = unit(e, nn)
        if runs and runs[-1]["ptype"] == u:
            runs[-1]["to_m"] = round(o)
        else:
            runs.append({"ptype": u, "from_m": round(o), "to_m": round(o)})
    legend = json.loads((assets / "geology_legend.json").read_text())
    colours = {u["ptype"]: u["color"] for u in legend["units"]}
    extra = mg.palette({r["ptype"] for r in runs if r["ptype"] and r["ptype"] not in colours})
    for r in runs:
        r["color"] = colours.get(r["ptype"]) or extra.get(r["ptype"])

    rivers = json.loads((assets / "rivers.json").read_text())
    out = {"id": site["id"], "name": site["name"], "vineyard": site.get("vineyard"), "region": site["region"],
           "location": dict(site["location"], utm=[round(e0, 1), round(n0, 1)]),
           "avas": avas_at(lat, lon, ROOT / region["boundary"]),
           "claims": site["claims"], "sources": site["sources"], "soil": soil,
           "geology": {"at_site": mg.unit_at(arcs, pat, e0, n0), "source": "S5", "label": legend["label"],
                       "limits": "1:100,000 map: contacts are good to about 50 m; units narrower than that are not shown."},
           "section": {"bearing_deg": 50, "half_m": half, "step_m": step,
                       "note": "SW (left) to NE (right) through the site, the viewer's section direction",
                       "ground_m": [round(g, 1) for g in ground], "units": runs,
                       "streams": stream_crossings(rivers, e0, n0, half),
                       "terrain": {"file": f"detail/{site['id']}", "source": "S7", "cell_m": meta["cell_m"]}}}
    (assets / "sites").mkdir(exist_ok=True)
    (assets / "sites" / f"{site['id']}.json").write_text(json.dumps(out, indent=1) + "\n")
    idx_path = assets / "sites" / "index.json"
    idx = json.loads(idx_path.read_text()) if idx_path.exists() else {"sites": []}
    idx["sites"] = [s for s in idx["sites"] if s["id"] != site["id"]] + [
        {"id": site["id"], "name": site["name"], "vineyard": site.get("vineyard"), "file": f"sites/{site['id']}.json",
         "utm": [round(e0, 1), round(n0, 1)], "closeup": site["id"]}]
    idx_path.write_text(json.dumps(idx, indent=1) + "\n")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site")
    ap.add_argument("--e00", required=True, help="SIM 2956 eswn-geol.e00 (owner-supplied)")
    ap.add_argument("--half", type=float, default=1900.0, help="half length of the section line (m)")
    ap.add_argument("--step", type=float, default=10.0, help="sample spacing along the line (m)")
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    s = build(a.site, a.e00, a.half, a.step, a.offline)
    sec = s["section"]
    print(f"{s['name']}: AVAs {', '.join(v['name'] for v in s['avas'])}; geology at site {s['geology']['at_site']}; "
          f"soil {s['soil']['series_name']} ({len(s['soil']['horizons'])} horizons)")
    print("  section units: " + ", ".join(f"{r['ptype'] or '-'} {r['from_m']}..{r['to_m']}" for r in sec["units"]))
    print("  streams: " + ", ".join(f"{c['name'] or 'unnamed'} @{c['offset_m']} m" for c in sec["streams"]))
    print(f"  ground {min(sec['ground_m']):.0f}..{max(sec['ground_m']):.0f} m")


if __name__ == "__main__":
    main()
