#!/usr/bin/env python3
"""Write a GeoLibre project for each region, so the viewer's evidence layers open in a real GIS.

GeoLibre (github.com/opengeos/GeoLibre, MIT) is a free, browser-based GIS. A project is one JSON file
(docs/project-format.md there); ours carry their GeoJSON inline, so a single URL opens everything:
  https://web.geolibre.app/?url=<raw GitHub URL of prototype/assets/geolibre/<id>.geolibre.json>
The viewer's "Open in GeoLibre" button builds that link from assets/geolibre/index.json.

Present-day evidence only, nothing reconstructed: AVA outlines (UC Davis AVA Project, CC0), mapped
fault traces (USGS UCERF3 via the GEM Global Active Faults Database, CC BY-SA 4.0, read from the
viewer's FAULTS table) and the viewer's frame box. A mapped region uses its full-resolution outline
(data/ava/<id>_avas.geojson); a planned one uses the simplified statewide outlines in
prototype/assets/globe/ca_avas.json.

Tier 0, stdlib only. Usage: geolibre_export.py [--regions napa_valley,sonoma_valley] [--ref main]
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_tiles import geographic_from_utm  # noqa: E402

VIEWER = ROOT / "prototype" / "timemachine.html"
CA_AVAS = ROOT / "prototype" / "assets" / "globe" / "ca_avas.json"
ORDER = ROOT / "prototype" / "assets" / "regions" / "order.json"
OUT = ROOT / "prototype" / "assets" / "geolibre"
REPO = "chachee1234/terroir-time-machine"
BASEMAP = "https://tiles.openfreemap.org/styles/liberty"   # GeoLibre's own default basemap, no key
VERSION = "0.1.0"                                          # GeoLibre project format version

# GeoLibre's default layer style (python/src/geolibre/project.py DEFAULT_LAYER_STYLE); ours override colours.
STYLE = {"minZoom": 0, "maxZoom": 24, "fillColor": "#3b82f6", "strokeColor": "#1e40af", "strokeWidth": 2,
         "fillOpacity": 0.6, "circleRadius": 6, "textColor": "#111827", "textHaloColor": "#ffffff",
         "textHaloWidth": 2, "textSize": 16, "extrusionEnabled": False, "extrusionColor": "#3b82f6",
         "extrusionOpacity": 0.8, "extrusionHeightProperty": "height", "extrusionHeightScale": 1,
         "extrusionBase": 0, "extrusionAdvancedStyleEnabled": False, "extrusionColorExpression": "",
         "extrusionHeightExpression": "", "vectorStyleMode": "single", "vectorStyleProperty": "",
         "vectorStyleClassCount": 5, "vectorStyleColorRamp": "viridis",
         "vectorStyleClassificationScheme": "equal-interval",
         "vectorStyleStops": [{"value": 0, "color": "#dbeafe"}, {"value": 1, "color": "#2563eb"}],
         "vectorStyleExpression": "", "pointRenderer": "single", "heatmapRadius": 30, "heatmapIntensity": 1,
         "heatmapColorRamp": "turbo", "heatmapWeightProperty": "", "clusterRadius": 50, "clusterMaxZoom": 14,
         "rasterBrightnessMin": 0, "rasterBrightnessMax": 1, "rasterSaturation": 0, "rasterContrast": 0,
         "rasterHueRotate": 0, "blendMode": "normal"}

FAULT_RIGHTS = ("USGS UCERF3 fault model traces via the GEM Global Active Faults Database (Styron & Pagani "
                "2020), CC BY-SA 4.0; credit GEM and USGS. Digitized for the Napa Valley frame only.")
AVA_RIGHTS = "UC Davis AVA Project (github.com/UCDavisLibrary/ava), CC0. Planning layer, not a legal boundary."


def rnd(c):
    return [round(c[0], 5), round(c[1], 5)]   # ~1 m, keeps the inline GeoJSON small


def round_geom(g):
    if g["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": [[rnd(p) for p in r] for r in g["coordinates"]]}
    if g["type"] == "MultiPolygon":
        return {"type": "MultiPolygon", "coordinates": [[[rnd(p) for p in r] for r in poly] for poly in g["coordinates"]]}
    raise ValueError(g["type"])


def rings_geom(rings):
    """ca_avas.json rings (lon/lat) -> GeoJSON; each ring becomes its own polygon."""
    polys = [[[rnd(p) for p in r] + ([rnd(r[0])] if r[0] != r[-1] else [])] for r in rings]
    return {"type": "Polygon", "coordinates": polys[0]} if len(polys) == 1 else {"type": "MultiPolygon", "coordinates": polys}


def viewer_faults(html=None):
    """The FAULTS table in timemachine.html (scene km, x east and z south of GNIS_UTM) as lon/lat lines."""
    html = html if html is not None else VIEWER.read_text()
    e0, n0 = map(float, re.search(r"const GNIS_UTM=\[([\d.]+),([\d.]+)\]", html).groups())
    block = re.search(r"const FAULTS=\[(.*?)\n\];", html, re.S).group(1)
    out = []
    for m in re.finditer(r'\{n:"([^"]+)", r:"([^"]+)",(?: k:(\d),)? pts:(\[\[.*?\]\])\}', block):
        name, rate, k, pts = m.group(1), m.group(2), m.group(3), json.loads(m.group(4))
        line = [rnd(geographic_from_utm(e0 + x * 1000, n0 - z * 1000)[::-1]) for x, z in pts]
        out.append({"type": "Feature", "properties": {"name": name, "slip_rate": rate,
                                                      "kind": "thrust" if k == "0" else "strike-slip",
                                                      "source": "USGS UCERF3 via GEM GAF-DB"},
                    "geometry": {"type": "LineString", "coordinates": line}})
    return out


REGION_FAULT_RIGHTS = ("USGS UCERF3 fault model traces via the GEM Global Active Faults Database (Styron & Pagani "
                      "2020), CC BY-SA 4.0; credit GEM and USGS. Clipped to this region by scripts/region_faults.py.")


def region_file_faults(rid):
    """The region's own faults.json (scripts/region_faults.py) as lon/lat lines, or None when it has none."""
    reg = ROOT / "data" / "regions" / f"{rid}.json"
    if not reg.exists():
        return None
    path = ROOT / json.loads(reg.read_text())["assets_dir"] / "faults.json"
    if not path.exists():
        return None
    out = []
    for q in json.loads(path.read_text())["faults"]:
        rate = q.get("net_slip_mm_yr") or [None]
        line = [rnd(geographic_from_utm(e * 1000, n * 1000)[::-1]) for e, n in q["pts_km"]]
        out.append({"type": "Feature", "properties": {"name": q.get("label") or q["name"], "catalog_id": q["id"],
                                                      "slip_rate": None if rate[0] is None else f"{rate[0]} mm/yr",
                                                      "kind": "thrust" if "reverse" in (q.get("slip_type") or "").lower() else "strike-slip",
                                                      "source": "USGS UCERF3 via GEM GAF-DB"},
                    "geometry": {"type": "LineString", "coordinates": line}})
    return out


def bbox_of(features):
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1])
        else:
            for q in c:
                walk(q)
    for f in features:
        walk(f["geometry"]["coordinates"])
    return [min(xs), min(ys), max(xs), max(ys)]


def near(f, bb, pad=0.1):
    x0, y0, x1, y1 = bbox_of([f])
    return not (x1 < bb[0] - pad or x0 > bb[2] + pad or y1 < bb[1] - pad or y0 > bb[3] + pad)


def layer(lid, name, features, **style):
    return {"id": lid, "name": name, "type": "geojson", "source": {"type": "geojson"}, "visible": True,
            "opacity": 1, "style": {**STYLE, **style}, "metadata": {},
            "geojson": {"type": "FeatureCollection", "features": features}}


def camera(bb):
    """Centre and a zoom that fits the box in a ~900 px map (Web Mercator, 512 px tiles as in MapLibre)."""
    cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    span = max(bb[2] - bb[0], (bb[3] - bb[1]) / math.cos(math.radians(cy)), 1e-3)
    z = max(3.0, min(14.0, math.log2(360 * 900 / 512 / span) - 0.3))
    return {"center": [round(cx, 5), round(cy, 5)], "zoom": round(z, 2), "bearing": 0, "pitch": 0,
            "bbox": [round(v, 5) for v in bb]}


def region_features(rid):
    """Outline and close-ups for one region: (name, outline features, close-up features, status, frame)."""
    reg = ROOT / "data" / "regions" / f"{rid}.json"
    if reg.exists():                                                   # mapped: full-resolution outlines
        r = json.loads(reg.read_text())
        fc = json.loads((ROOT / r["boundary"]).read_text())["features"]
        props = lambda p: {"name": p["name"], "ava_id": p["ava_id"], "established": p.get("created"),
                           "within": p.get("within"), "source": "UC Davis AVA Project"}
        parents = r.get("parents") or [rid]                           # frame-sized AVAs; the rest are close-ups
        main = [{"type": "Feature", "properties": props(f["properties"]), "geometry": round_geom(f["geometry"])}
                for f in fc if f["properties"]["ava_id"] in parents]
        subs = [{"type": "Feature", "properties": props(f["properties"]), "geometry": round_geom(f["geometry"])}
                for f in fc if f["properties"]["ava_id"] not in parents]
        x0, y0, x1, y1 = r["bbox_utm"]
        ring = [rnd(geographic_from_utm(e, n)[::-1]) for e, n in ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))]
        frame = {"type": "Feature", "properties": {"name": "Viewer 3D frame", "note": r["description"]},
                 "geometry": {"type": "Polygon", "coordinates": [ring]}}
        name = " and ".join(f["properties"]["name"] for f in main)
        return name, main, subs, "mapped", frame
    avas = {a["id"]: a for a in json.loads(CA_AVAS.read_text())["avas"]}
    if rid not in avas:
        raise SystemExit(f"unknown region {rid}")
    plan = {o["id"]: o for o in json.loads(ORDER.read_text())["order"]} if ORDER.exists() else {}
    feat = lambda a: {"type": "Feature", "properties": {"name": a["name"], "ava_id": a["id"], "within": a.get("within"),
                                                         "source": "UC Davis AVA Project (simplified)"},
                      "geometry": rings_geom(a["rings"])}
    subs = [feat(avas[c]) for c in plan.get(rid, {}).get("close_ups", []) if c in avas]
    return avas[rid]["name"], [feat(avas[rid])], subs, "planned", None


def project(rid, faults):
    name, main, subs, status, frame = region_features(rid)
    bb = bbox_of(main)
    layers = []
    if frame:
        layers.append(layer(f"ttm-{rid}-frame", "Viewer 3D frame (not geology)", [frame],
                            fillOpacity=0, strokeColor="#9aa3ad", strokeWidth=1.5))
    layers.append(layer(f"ttm-{rid}-ava", f"{name} AVA" + ("s" if len(main) > 1 else ""), main, fillColor="#ffd27a", fillOpacity=0.08,
                        strokeColor="#d9a520", strokeWidth=2.5))
    if subs:
        layers.append(layer(f"ttm-{rid}-subavas", "AVAs inside it" if status == "planned" else "Smaller AVAs in the frame", subs, fillColor="#7fd1a8", fillOpacity=0.12,
                            strokeColor="#2f9e6e", strokeWidth=1.5))
    own = region_file_faults(rid)
    near_f = own if own is not None else [f for f in faults if near(f, bb)]
    if near_f:
        layers.append(layer(f"ttm-{rid}-faults", "Mapped active faults (UCERF3)", near_f,
                            strokeColor="#ff5a3c", strokeWidth=2.5, fillOpacity=0))
    return {"version": VERSION, "name": f"Terroir Time Machine · {name}", "mapView": camera(bb),
            "basemapStyleUrl": BASEMAP, "basemapVisible": True, "basemapOpacity": 1, "layers": layers,
            "styles": {}, "metadata": {
                "generator": "terroir-time-machine scripts/geolibre_export.py",
                "region": rid, "status": status,
                "note": "Present-day evidence layers from the Terroir Time Machine viewer. Nothing here is a "
                        "reconstruction of the past.",
                "sources": [AVA_RIGHTS] + ([REGION_FAULT_RIGHTS if own is not None else FAULT_RIGHTS] if near_f else [])}}


def link(rid, ref):
    return (f"https://web.geolibre.app/?url=https://raw.githubusercontent.com/{REPO}/{ref}"
            f"/prototype/assets/geolibre/{rid}.geolibre.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regions", default="napa_valley,sonoma_valley")
    ap.add_argument("--ref", default="main", help="git branch the viewer's links point at")
    a = ap.parse_args()
    faults = viewer_faults()
    OUT.mkdir(parents=True, exist_ok=True)
    ids = [r for r in a.regions.split(",") if r]
    for rid in ids:
        p = project(rid, faults)
        path = OUT / f"{rid}.geolibre.json"
        path.write_text(json.dumps(p, separators=(",", ":")) + "\n")
        print(f"{path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB  layers: "
              + ", ".join(f"{l['name']} ({len(l['geojson']['features'])})" for l in p["layers"]))
    (OUT / "index.json").write_text(json.dumps({"repo": REPO, "ref": a.ref, "regions": ids,
                                                "open": "https://web.geolibre.app/?url=https://raw.githubusercontent.com/{repo}/{ref}/prototype/assets/geolibre/{id}.geolibre.json"},
                                               indent=1) + "\n")
    print(link(ids[0], a.ref))


if __name__ == "__main__":
    main()
