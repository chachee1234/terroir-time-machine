#!/usr/bin/env python3
"""Active fault traces for a region frame, as region data (Tier 0, stdlib only).

Input: the GEM Global Active Faults Database `gem_active_faults_harmonized.geojson` (CC BY-SA 4.0;
SOURCES.md G17), whose California traces come from the USGS UCERF3 fault model. Downloaded with
curl unless --from-file is given. Every trace with at least one vertex inside the region's
bbox_utm is kept whole (the viewer clips at the frame edge), with the catalog's own attributes.

Output: <assets_dir>/faults.json, vertices in NAD83 / UTM zone 10N kilometres (WGS84 input
treated as NAD83, sub-metre difference ignored), plus a data/manifest.json entry.

Usage: region_faults.py --region data/regions/petaluma_gap.json [--from-file PATH]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_terrain import utm_from_geographic  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
URL = "https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/master/geojson/gem_active_faults_harmonized.geojson"
RIGHTS = "CC BY-SA 4.0 (GEM Global Active Faults Database, Styron & Pagani 2020); California traces from USGS UCERF3"


def triple(s):
    """GEM stores '(best,min,max)' strings with empty slots; return [best, min, max] as floats or None."""
    if not s:
        return None
    out = [float(v) if v.strip() else None for v in str(s).strip("()").split(",")]
    return out if any(v is not None for v in out) else None


def lines_of(geom):
    if not geom:
        return []
    return geom["coordinates"] if geom["type"] == "MultiLineString" else [geom["coordinates"]]


def select(features, frame):
    """Traces with a vertex inside frame [e0, n0, e1, n1], sorted by catalog id."""
    e0, n0, e1, n1 = frame
    out = []
    for f in features:
        p = f["properties"]
        for line in lines_of(f["geometry"]):
            pts = [utm_from_geographic(lat, lon) for lon, lat, *_ in line]
            if not any(e0 <= x <= e1 and n0 <= y <= n1 for x, y in pts):
                continue
            rate = triple(p.get("net_slip_rate"))
            dip = triple(p.get("average_dip"))
            name = (p.get("name") or "").strip()
            out.append({"id": p.get("catalog_id"), "name": name, "label": name.replace(" 2011 CFM", "").strip(),
                        "catalog": p.get("catalog_name"),
                        "slip_type": p.get("slip_type"), "dip_deg": dip[0] if dip else None,
                        "net_slip_mm_yr": rate, "pts_km": [[round(x / 1000, 3), round(y / 1000, 3)] for x, y in pts]})
    return sorted(out, key=lambda q: (q["id"] or "", q["pts_km"][0]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--region", required=True, help="region file")
    ap.add_argument("--from-file", help="use a local copy of the GEM geojson")
    a = ap.parse_args(argv)
    buf = Path(a.from_file).read_bytes() if a.from_file else \
        subprocess.run(["curl", "-sSf", "--max-time", "300", URL], check=True, capture_output=True).stdout
    sha = hashlib.sha256(buf).hexdigest()
    region = json.loads((ROOT / a.region).read_text())
    faults = select(json.loads(buf)["features"], region["bbox_utm"])
    out = ROOT / region["assets_dir"] / "faults.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"region": region["id"], "source": "GEM Global Active Faults Database", "url": URL,
                               "rights": RIGHTS, "source_sha256": sha,
                               "crs": "EPSG:26910 (NAD83 / UTM zone 10N) kilometres; WGS84 input treated as NAD83",
                               "rule": "every trace with a vertex inside bbox_utm, kept whole",
                               "note": "fault-model traces (simplified), not field-mapped surface ruptures",
                               "faults": faults}, indent=1) + "\n")
    man_path = ROOT / "data" / "manifest.json"
    man = json.loads(man_path.read_text()) if man_path.exists() else {"datasets": []}
    mid = f"{region['id']}-faults"
    man["datasets"] = [d for d in man["datasets"] if d.get("id") != mid]
    man["datasets"].append({"id": mid, "source": "GEM Global Active Faults Database", "url": URL, "rights": RIGHTS,
                            "source_sha256": sha, "derived": [{"file": str(out.relative_to(ROOT)),
                                                               "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}]})
    man_path.write_text(json.dumps(man, indent=2) + "\n")
    print(f"{region['id']}: {len(faults)} traces: " + ", ".join(f"{q['name']} ({q['id']})" for q in faults))


if __name__ == "__main__":
    main()
