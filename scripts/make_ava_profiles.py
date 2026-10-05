"""AVA profiles for the description card: elevation, area, geology, soils, vineyard acres, producers (Tier 0).

    python3 scripts/make_ava_profiles.py --region data/regions/napa_valley.json \
        --metadata data/raw/sim2956d.met.txt [--no-soils]

Writes prototype/assets/regions/<region>/ava_profiles.json, one record per AVA that has a close-up:
  elevation   min / 10th percentile / median / 90th percentile / max of the close-up DEM inside the AVA outline
              (AWS Terrain Tiles, USGS 3DEP source, 10-50 m cells; SOURCES.md G19)
  area_km2    of the outline (UC Davis AVA Project, G18; simplified to 25 m)
  geology     share of the outline in each USGS SIM 2956 unit, from the close-up's geology grid (G07/G27), with
              the unit's name from the map's FGDC metadata (Attribute_Domain_Values, source "author")
  soils       share of the outline in each USDA SSURGO map unit, grouped by the map unit's soil name
              (Soil Data Access, area of intersection; G33), and the share that is gravelly or cobbly, clay,
              loam or rock outcrop by map-unit name
  vineyards   USDA CDL grape acres inside the AVA, latest year (vineyards.json, G30)
  producers   from data/ava_producers.json, each with its source URL (hand-gathered; not computed)

Percentages describe the mapped area, not vineyards: a hillside AVA's soils are mostly under forest and chaparral.
"""
import argparse
import json
import math
import struct
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_tiles import decode_png_rgb  # noqa: E402
from make_geology_texture import GRS80, utm_inverse  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SDA = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"


def unit_names(met_path):
    """ptype -> definition from the SIM 2956 FGDC metadata (Enumerated_Domain_Value pairs)."""
    names, cur = {}, None
    for line in Path(met_path).read_text(errors="replace").splitlines():
        s = line.strip()
        if s.startswith("Enumerated_Domain_Value:"):
            cur = s.split(":", 1)[1].strip()
        elif s.startswith("Enumerated_Domain_Value_Definition:") and cur:
            d = s.split(":", 1)[1].strip()
            if d and cur not in names:
                names[cur] = d
            cur = None
    return names


def ring_mask(rings, e0, n1, cell, cols, rows):
    """Grid points (row 0 north, centred on e0 + c*cell, n1 - r*cell) inside the polygon (even-odd over rings, metres)."""
    inside = bytearray(cols * rows)
    edges = []
    for ring in rings:
        pts = [(x * 1000, y * 1000) for x, y in ring]
        for i in range(len(pts)):
            edges.append((pts[i - 1], pts[i]))
    for r in range(rows):
        y = n1 - r * cell
        xs = sorted(x0 + (y - y0) * (x1 - x0) / (y1 - y0) for (x0, y0), (x1, y1) in edges if (y0 > y) != (y1 > y))
        for a, b in zip(xs[0::2], xs[1::2]):
            c0, c1 = max(0, math.ceil((a - e0) / cell)), min(cols - 1, math.floor((b - e0) / cell))
            for c in range(c0, c1 + 1):
                inside[r * cols + c] = 1
    return inside


def polygon_area_km2(rings):
    a = 0.0
    for ring in rings:
        a += sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1])) / 2
    return abs(a)


def pct(values, q):
    i = min(len(values) - 1, max(0, round(q * (len(values) - 1))))
    return values[i]


def sda(query, tries=3):
    body = json.dumps({"query": query, "format": "JSON"}).encode()
    for k in range(tries):
        try:
            req = urllib.request.Request(SDA, data=body, headers={"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=180).read() or b"{}").get("Table", [])
        except Exception as e:  # noqa: BLE001 - network: retry, then give up on this AVA
            err = e
            time.sleep(2 * (k + 1))
    raise RuntimeError(f"SDA failed: {err}")


def soil_name(muname):
    """'Bale clay loam, 0 to 2 percent slopes' -> 'Bale clay loam'; complexes keep their names."""
    return muname.split(",")[0].strip()


def soils_for(rings):
    wkt_rings = []
    for ring in rings:
        pts = [utm_inverse(x * 1000, y * 1000, GRS80) for x, y in ring]
        pts.append(pts[0])
        wkt_rings.append("(" + ",".join(f"{math.degrees(lo):.6f} {math.degrees(la):.6f}" for la, lo in pts) + ")")
    wkt = "MULTIPOLYGON(" + ",".join("(" + r + ")" for r in wkt_rings) + ")" if len(wkt_rings) > 1 else "POLYGON(" + wkt_rings[0] + ")"
    q = f"""~DeclareGeometry(@aoi)~
select @aoi = geometry::STGeomFromText('{wkt}', 4326).MakeValid()
SELECT mu.mukey, mu.muname, SUM(m.mupolygongeo.STIntersection(@aoi).STArea()) AS a
FROM mupolygon m JOIN mapunit mu ON mu.mukey=m.mukey
WHERE m.mupolygongeo.STIntersects(@aoi)=1 GROUP BY mu.mukey, mu.muname"""
    rows = [(r[1], float(r[2])) for r in sda(q)]
    tot = sum(a for _, a in rows) or 1
    by = {}
    for nm, a in rows:
        by[soil_name(nm)] = by.get(soil_name(nm), 0) + a
    top = sorted(by.items(), key=lambda kv: -kv[1])
    groups = {"gravelly or cobbly": ("gravel", "cobbl", "stony"), "clay": ("clay",), "rock outcrop": ("rock outcrop", "rock-outcrop", "rock land"), "water": ("water",)}
    share = {g: round(100 * sum(a for nm, a in rows if any(k in nm.lower() for k in keys)) / tot) for g, keys in groups.items()}
    return {"map_units": [{"name": n, "pct": round(100 * a / tot, 1)} for n, a in top[:6]],
            "n_names": len(top), "share_by_name": share}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--region", required=True, type=Path)
    ap.add_argument("--metadata", type=Path, default=ROOT / "data/raw/sim2956d.met.txt")
    ap.add_argument("--producers", type=Path, default=ROOT / "data/ava_producers.json")
    ap.add_argument("--no-soils", action="store_true", help="skip the USDA Soil Data Access queries (offline)")
    ap.add_argument("--only", help="comma-separated AVA ids")
    args = ap.parse_args()

    region = json.loads(args.region.read_text())
    rid = region.get("id") or args.region.stem
    assets = ROOT / "prototype/assets/regions" / rid
    out_path = assets / "ava_profiles.json"
    old = json.loads(out_path.read_text()) if out_path.exists() else {"avas": {}}
    avas = {a["id"]: a for a in json.loads((ROOT / "prototype/assets/ava.json").read_text())["avas"]}
    index = json.loads((assets / "detail/index.json").read_text())["locations"]
    geo = {c["id"]: c for c in json.loads((assets / "detail/geology.json").read_text())["closeups"]}
    names = unit_names(args.metadata) if args.metadata.exists() else {}
    vy = json.loads((assets / "vineyards.json").read_text()) if (assets / "vineyards.json").exists() else None
    vyear = max(vy["years"]) if vy else None
    producers = json.loads(args.producers.read_text()) if args.producers.exists() else {"avas": {}}
    only = set(args.only.split(",")) if args.only else None

    out = {"region": rid, "built": time.strftime("%Y-%m-%d"),
           "sources": {"elevation": "AWS Terrain Tiles (USGS 3DEP source), each AVA's close-up grid (SOURCES.md G19)",
                       "outline": "UC Davis AVA Project (G18), simplified to 25 m",
                       "geology": "USGS SIM 2956, 1:100,000 (G07); unit names from its FGDC metadata",
                       "soils": "USDA-NRCS SSURGO via Soil Data Access, map-unit area inside the outline (G33)",
                       "vineyards": f"USDA NASS Cropland Data Layer {vyear}, grapes (G30)" if vy else None,
                       "producers": "data/ava_producers.json: " + producers.get("status", "hand-gathered") + "; each AVA lists its source pages"},
           "limits": "Shares are of the whole AVA outline, not of its vineyards. Geology at 1:100,000; SSURGO at about 1:24,000; CDL is a satellite classification.",
           "avas": {}}
    for loc in index:
        if loc.get("kind", "ava") != "ava" or loc["id"] not in avas:
            continue
        aid, a = loc["id"], avas[loc["id"]]
        if only and aid not in only:
            out["avas"][aid] = old["avas"].get(aid)
            continue
        base = assets / loc["file"]                       # "detail/<id>": <id>.json + <id>.bin
        meta = json.loads(base.with_suffix(".json").read_text())
        cols, rows, cell, sc = meta["cols"], meta["rows"], meta["cell_m"], meta.get("scale", 1)
        b = meta["bbox_utm"]
        h = struct.unpack(f"<{cols * rows}h", base.with_suffix(".bin").read_bytes())
        mask = ring_mask(a["rings"], b[0], b[3], cell, cols, rows)
        el = sorted(h[i] * sc for i in range(cols * rows) if mask[i] and h[i] > -32000)
        rec = {"name": a["name"], "established": a.get("created"), "cfr": a.get("cfr"),
               "area_km2": round(polygon_area_km2(a["rings"]), 1),
               "elevation_m": {"min": round(el[0]), "p10": round(pct(el, 0.1)), "median": round(pct(el, 0.5)),
                               "p90": round(pct(el, 0.9)), "max": round(el[-1]), "cell_m": cell} if el else None}
        g = geo.get(aid)
        if g:
            gw, gh, bpp, rgba = decode_png_rgb((assets / "detail" / g["file"]).read_bytes())
            if (gw, gh, bpp) != (cols, rows, 4):
                raise SystemExit(f"{aid}: geology grid {gw}x{gh} does not match the close-up {cols}x{rows}")
            col = {tuple(int(u["color"][k:k + 2], 16) for k in (1, 3, 5)): u["ptype"] for u in g["units"]}
            cnt, n = {}, 0
            for i in range(cols * rows):
                if not mask[i] or rgba[i * 4 + 3] < 128:
                    continue
                u = col.get(tuple(rgba[i * 4:i * 4 + 3]))
                if u:
                    cnt[u] = cnt.get(u, 0) + 1
                    n += 1
            rec["geology"] = [{"ptype": u, "name": names.get(u, ""), "pct": round(100 * c / n, 1)}
                              for u, c in sorted(cnt.items(), key=lambda kv: -kv[1])[:6] if 100 * c / n >= 2] if n else []
        if not args.no_soils:
            try:
                rec["soils"] = soils_for(a["rings"])
            except RuntimeError as e:
                print(f"{aid}: {e}", file=sys.stderr)
                rec["soils"] = (old["avas"].get(aid) or {}).get("soils")
        else:
            rec["soils"] = (old["avas"].get(aid) or {}).get("soils")
        if vy:
            rec["vineyard_acres"] = {"year": vyear, "acres": vy["years"][vyear]["ava_acres"].get(a["name"])}
        rec["producers"] = producers["avas"].get(aid)
        out["avas"][aid] = rec
        e = rec["elevation_m"] or {}
        print(f"{aid:40s} {rec['area_km2']:7.1f} km2  {e.get('min')}-{e.get('max')} m  "
              f"geo {','.join(x['ptype'] for x in rec.get('geology', [])[:3])}  "
              f"soil {((rec.get('soils') or {}).get('map_units') or [{}])[0].get('name')}")
    out_path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
