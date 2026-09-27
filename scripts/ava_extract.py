#!/usr/bin/env python3
"""Extract the Napa Valley AVA and the AVAs nested in it from the UC Davis AVA Project.

Tier 0, stdlib only. Input: the project's aggregated `avas.geojson` (CC0), downloaded with curl
unless --from-file is given. Outputs:
  data/ava/napa_valley_avas.geojson   full-resolution boundaries, trimmed properties (WGS84)
  prototype/assets/ava.json           simplified outlines in UTM zone 10N kilometres for the viewer
  data/manifest.json                  source URL and SHA-256 of both files

Usage: ava_extract.py [--from-file PATH] [--tolerance-m 25]
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
URL = "https://raw.githubusercontent.com/UCDavisLibrary/ava/master/avas_aggregated_files/avas.geojson"
PARENT = "napa_valley"
KEEP = ("ava_id", "name", "created", "within", "cfr_index", "valid_end")


def select(features):
    """Current (valid_end is null) Napa Valley AVA plus every current AVA listed as within it."""
    out = []
    for f in features:
        p = f["properties"]
        if p.get("valid_end"):
            continue
        if p.get("ava_id") == PARENT or "Napa Valley" in (p.get("within") or "").split("|"):
            out.append({"type": "Feature", "properties": {k: p.get(k) for k in KEEP}, "geometry": f["geometry"]})
    return sorted(out, key=lambda f: (f["properties"]["ava_id"] != PARENT, f["properties"]["ava_id"]))


def simplify(pts, tol):
    """Douglas-Peucker on a planar ring or line (iterative)."""
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = pts[a], pts[b]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = pts[i]
            if L2 == 0:
                d = (px - ax) ** 2 + (py - ay) ** 2
            else:
                t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
                d = (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2
            if d > best:
                best, bi = d, i
        if bi >= 0 and best > tol * tol:
            keep[bi] = True
            stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [ring for poly in polys for ring in poly]


def to_viewer(features, tol_m):
    avas = []
    for f in features:
        p = f["properties"]
        out_rings = []
        for ring in rings(f["geometry"]):
            utm = [utm_from_geographic(lat, lon) for lon, lat, *_ in ring]
            s = simplify(utm, tol_m)
            if len(s) >= 4:
                out_rings.append([[round(x / 1000, 3), round(y / 1000, 3)] for x, y in s])
        avas.append({"id": p["ava_id"], "name": p["name"], "created": p["created"], "cfr": p["cfr_index"], "rings": out_rings})
    return avas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-file", help="use a local copy of avas.geojson")
    ap.add_argument("--tolerance-m", type=float, default=25.0, help="simplification tolerance for the viewer file")
    args = ap.parse_args()
    buf = Path(args.from_file).read_bytes() if args.from_file else \
        subprocess.run(["curl", "-sSf", "--max-time", "300", URL], check=True, capture_output=True).stdout
    src_sha = hashlib.sha256(buf).hexdigest()
    feats = select(json.loads(buf)["features"])
    if not feats or feats[0]["properties"]["ava_id"] != PARENT:
        sys.exit("Napa Valley AVA not found in the input")

    full = ROOT / "data" / "ava" / "napa_valley_avas.geojson"
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")) + "\n")
    viewer = ROOT / "prototype" / "assets" / "ava.json"
    meta = {"source": "UC Davis Library & DataLab, American Viticultural Areas (AVA) Project", "url": URL,
            "rights": "CC0 1.0", "source_sha256": src_sha,
            "crs": "EPSG:26910 (NAD83 / UTM zone 10N) kilometres; WGS84 input treated as NAD83 (sub-metre difference ignored)",
            "simplification_m": args.tolerance_m, "avas": to_viewer(feats, args.tolerance_m)}
    viewer.write_text(json.dumps(meta, separators=(",", ":")) + "\n")

    manifest_path = ROOT / "data" / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"datasets": []}
    manifest["datasets"] = [d for d in manifest["datasets"] if d.get("id") != "ava-napa-valley"]
    manifest["datasets"].append({"id": "ava-napa-valley", "source": meta["source"], "url": URL, "rights": "CC0 1.0",
                                 "source_sha256": src_sha,
                                 "derived": [{"file": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                                             for p in (full, viewer)]})
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{len(feats)} AVAs: " + ", ".join(f["properties"]["name"] for f in feats))


if __name__ == "__main__":
    main()
