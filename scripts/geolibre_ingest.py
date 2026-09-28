#!/usr/bin/env python3
"""Read a region mapped in GeoLibre and turn its layers into Terroir Time Machine evidence files.

GeoLibre (github.com/opengeos/GeoLibre, MIT) is where sources are found and mapped: its catalog panels
reach the USGS National Map, NRCS soils, the California state GIS portal and STAC imagery. GeoLibre is
the finder, never the citation: the agency service a layer came from stays its source of record.

Workflow (owner decision, 2026-09-28):
  1. Open the region's starter project (prototype/assets/geolibre/<id>.geolibre.json, geolibre_export.py)
     in GeoLibre, add source layers, and name each one with its role first: "soils: SSURGO map units",
     "geology: CGS 1:100k", "faults: ...", "vineyards: ...", "places: ...". Layers without a role
     prefix (the starter's own outlines) are ignored.
  2. Save the project as data/geolibre/<region_id>.geolibre (vector layers need their features saved
     in the file: download a feature service as GeoJSON first if GeoLibre only linked it).
  3. Run this script. Each role layer gets a verdict from its source URL:
       accepted      the host is an allowed open source (AUTOPILOT.md "Allowed sources")
       needs_review  no URL, or a host we can't vouch for (e.g. ArcGIS Online hosting); the owner can
                     accept it in data/geolibre/<region_id>.sources.json
       rejected      Esri imagery/basemaps, parcel data, or a URL carrying a key or token
     Accepted layers are written to data/intake/<region_id>/<role>.geojson (features that touch the
     region's frame; features are kept whole, not cut) and registered in data/manifest.json as
     "pending_verification" until SOURCES.md records the licence.

Sidecar data/geolibre/<region_id>.sources.json (optional, owner-written):
  {"soils: SSURGO map units": {"url": "https://...", "licence": "public domain", "owner_accepted": true}}

Tier 0, stdlib only. Usage: geolibre_ingest.py data/geolibre/<region_id>.geolibre [--dry-run]
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetch_tiles import geographic_from_utm  # noqa: E402

ROLES = {"soils": ("Polygon", "MultiPolygon"), "geology": ("Polygon", "MultiPolygon"),
         "vineyards": ("Polygon", "MultiPolygon"), "faults": ("LineString", "MultiLineString"),
         "places": ("Point", "MultiPoint")}
# Open sources named in AUTOPILOT.md "Allowed sources" and SOURCES.md, by host (suffix match).
ALLOWED_HOSTS = ("usgs.gov", "nationalmap.gov", "usda.gov", "ca.gov", "earth-search.aws.element84.com",
                 "sentinel-cogs.s3.us-west-2.amazonaws.com", "elevation-tiles-prod.s3.amazonaws.com")
ALLOWED_PREFIXES = ("https://raw.githubusercontent.com/UCDavisLibrary/", "https://raw.githubusercontent.com/GEMScienceTools/",
                    "https://github.com/UCDavisLibrary/", "https://github.com/GEMScienceTools/")
BLOCKED = [(re.compile(r"arcgisonline\.com|World_Imagery", re.I), "Esri imagery or basemap"),
           (re.compile(r"parcel", re.I), "parcel data"),
           (re.compile(r"[?&](api_?key|key|token|access_token|apikey)=", re.I), "URL carries a key or token")]
URL_RE = re.compile(r"https?://[^\s\"'<>]+")


def layer_urls(layer):
    """Every URL GeoLibre recorded for a layer (sourcePath, source.*, metadata.*), features excluded."""
    found = []

    def walk(v):
        if isinstance(v, str):
            found.extend(URL_RE.findall(v))
        elif isinstance(v, dict):
            for k, x in v.items():
                if k not in ("geojson", "embeddedGeoJSON", "style", "popup"):
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk({k: layer.get(k) for k in ("sourcePath", "source", "metadata", "connection")})
    return list(dict.fromkeys(found))


def verdict(name, urls, override=None):
    """(status, reason, url) for one layer."""
    if override and override.get("url"):
        urls = [override["url"]] + urls
    for u in urls:
        for rx, why in BLOCKED:
            if rx.search(u):
                return "rejected", why, u
    if "parcel" in name.lower():
        return "rejected", "parcel data", urls[0] if urls else None
    for u in urls:
        host = (urlparse(u).hostname or "").lower()
        if any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS) or u.startswith(ALLOWED_PREFIXES):
            return "accepted", f"allowed source ({host})", u
    if override and override.get("owner_accepted"):
        return "accepted", "accepted by the owner in the sources file", urls[0] if urls else None
    if not urls:
        return "needs_review", "no source URL recorded; add one in the sources file", None
    return "needs_review", f"host not on the allowed list ({urlparse(urls[0]).hostname})", urls[0]


def frame_lonlat(rid):
    """The region's frame as [west, south, east, north]: the viewer frame if mapped, else the AVA box + ~2 km."""
    reg = ROOT / "data" / "regions" / f"{rid}.json"
    if reg.exists():
        x0, y0, x1, y1 = json.loads(reg.read_text())["bbox_utm"]
        pts = [geographic_from_utm(e, n) for e, n in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        return [min(p[1] for p in pts), min(p[0] for p in pts), max(p[1] for p in pts), max(p[0] for p in pts)]
    for a in json.loads((ROOT / "prototype" / "assets" / "globe" / "ca_avas.json").read_text())["avas"]:
        if a["id"] == rid:
            xs = [p[0] for r in a["rings"] for p in r]; ys = [p[1] for r in a["rings"] for p in r]
            return [min(xs) - 0.025, min(ys) - 0.02, max(xs) + 0.025, max(ys) + 0.02]
    raise SystemExit(f"unknown region {rid}: no data/regions/{rid}.json and no AVA with that id")


def coords_bbox(c):
    xs, ys = [], []

    def walk(q):
        if q and isinstance(q[0], (int, float)):
            xs.append(q[0]); ys.append(q[1])
        else:
            for r in q:
                walk(r)
    walk(c)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def touches(f, fr):
    b = coords_bbox((f.get("geometry") or {}).get("coordinates") or [])
    return bool(b) and not (b[2] < fr[0] or b[0] > fr[2] or b[3] < fr[1] or b[1] > fr[3])


def role_of(name):
    m = re.match(r"\s*([a-z]+)\s*:\s*(.+)", name, re.I)
    return (m.group(1).lower(), m.group(2).strip()) if m and m.group(1).lower() in ROLES else (None, name)


def ingest(project_path, dry_run=False, root=ROOT):
    project_path = Path(project_path)
    rid = re.sub(r"\.geolibre(\.json)?$", "", project_path.name)
    if not re.fullmatch(r"[a-z0-9_]+", rid):
        raise SystemExit(f"file name must be <region_id>.geolibre, got {project_path.name}")
    proj = json.loads(project_path.read_text())
    if not all(k in proj for k in ("version", "name", "mapView")):
        raise SystemExit("not a GeoLibre project (version, name and mapView are required)")
    side = project_path.with_name(f"{rid}.sources.json")
    overrides = json.loads(side.read_text()) if side.exists() else {}
    fr = frame_lonlat(rid)
    report, written = [], []
    for layer in proj.get("layers", []):
        role, title = role_of(layer.get("name", ""))
        if not role:
            continue
        ov = overrides.get(layer["name"])
        status, why, url = verdict(layer["name"], layer_urls(layer), ov)
        feats = ((layer.get("geojson") or {}).get("features")) or []
        row = {"layer": layer["name"], "role": role, "status": status, "reason": why, "source_url": url,
               "features_in_file": len(feats)}
        if status == "accepted":
            good = [f for f in feats if (f.get("geometry") or {}).get("type") in ROLES[role]]
            keep = [f for f in good if touches(f, fr)]
            row.update(wrong_geometry=len(feats) - len(good), kept=len(keep))
            if not feats:
                row.update(status="needs_review", reason="no features saved in the file; download the layer as GeoJSON in GeoLibre")
            elif not keep:
                row.update(status="needs_review", reason="no features of the right type touch the region frame")
            elif not dry_run:
                out = root / "data" / "intake" / rid / f"{role}.geojson"
                out.parent.mkdir(parents=True, exist_ok=True)
                fc = {"type": "FeatureCollection", "name": title, "source_url": url,
                      "note": "Imported from a GeoLibre project; features touching the region frame, kept whole.",
                      "features": keep}
                out.write_text(json.dumps(fc, separators=(",", ":")) + "\n")
                written.append((role, title, url, (ov or {}).get("licence"), out))
        report.append(row)
    if written and not dry_run:
        register(rid, project_path, written, root)
    return {"region": rid, "frame": [round(v, 5) for v in fr], "layers": report}


def register(rid, project_path, written, root=ROOT):
    mpath = root / "data" / "manifest.json"
    man = json.loads(mpath.read_text())
    new_ids = {f"geolibre-{rid}-{r}" for r, *_ in written}
    ds = [d for d in man["datasets"] if d["id"] not in new_ids]   # a re-import replaces its entry
    for role, title, url, lic, out in written:
        ds.append({"id": f"geolibre-{rid}-{role}", "source": title, "url": url, "via": "GeoLibre project "
                   + str(project_path.relative_to(root) if project_path.is_relative_to(root) else project_path.name),
                   "fetched": date.today().isoformat(), "rights": lic or "unverified",
                   "status": "pending_verification",
                   "derived": [{"file": str(out.relative_to(root)), "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}]})
    man["datasets"] = ds
    mpath.write_text(json.dumps(man, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--dry-run", action="store_true", help="report verdicts, write nothing")
    a = ap.parse_args()
    r = ingest(a.project, a.dry_run)
    print(f"{r['region']}  frame {r['frame']}")
    for row in r["layers"]:
        extra = f"  kept {row['kept']}/{row['features_in_file']}" if "kept" in row else ""
        print(f"  {row['status']:<13} {row['layer']:<40} {row['reason']}{extra}")
    if not r["layers"]:
        print("  no role layers found (name them 'soils: ...', 'geology: ...', 'faults: ...', 'vineyards: ...', 'places: ...')")


if __name__ == "__main__":
    main()
