"""Soil layers from the USDA soil survey (SSURGO, via Soil Data Access), Tier 0, standard library only.

For one or more map units (mukey), every component (the named soils a map unit is made of, with their share)
and each component's layers (horizons) with the survey's representative values:
  sand, silt, clay   percent of the fine earth (particles under 2 mm)
  om                 organic matter, percent
  pH                 1:1 in water
  awc                available water capacity, cm of water per cm of soil
  ksat               saturated hydraulic conductivity, micrometres per second
  rock_frag          rock fragments over 2 mm (gravel, cobbles), percent by volume (sum of chfrags)
  texture            the survey's texture for the layer ("Gravelly loam")
plus the component's drainage class and taxonomic class, and the survey area and its version date.

Representative values are the survey's typical numbers for that soil across its mapped area, not a sample
taken at one spot. Survey scale is about 1:24,000: a map unit can hold small areas of other soils.

    python3 scripts/ssurgo_layers.py --point 38.484983 -122.44736 [--radius 150]

Frame mode: every map unit of the given survey areas (default Napa CA055 and Sonoma CA097) inside a region frame,
rasterized onto the frame's 30 m grid, with each unit's components and layers:

    python3 scripts/ssurgo_layers.py --frame data/regions/napa_valley.json

writes <assets_dir>/soils.png (map unit per 30 m cell, north up; R*256+G = 1 + index into soils.json "units",
alpha 0 where these surveys have no map unit) and <assets_dir>/soils.json (per unit: name, slope class, components
with %, drainage, depth to a restrictive layer and layers with depth, texture, sand/silt/clay, gravel, rock
fragments, organic matter, pH, available water; plus a colour per soil series for the Soils drape).

Answers are cached in data/raw/ssurgo/ (git-ignored), so a rebuild works offline once fetched.
"""
import argparse
import array
import colorsys
import hashlib
import json
import math
import re
import struct
import sys
import time
import urllib.request
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from net import open_url  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SDA = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"
CACHE = ROOT / "data" / "raw" / "ssurgo"
SOURCE = {"title": "USDA-NRCS Soil Survey Geographic Database (SSURGO), via Soil Data Access",
          "url": "https://sdmdataaccess.sc.egov.usda.gov", "kind": "soil survey, about 1:24,000 (US public domain)"}


def sda(query, offline=False, tries=3):
    """Rows of a Soil Data Access query (list of lists, strings or None), cached by the query text."""
    key = hashlib.sha256(query.encode()).hexdigest()[:20]
    path = CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    if offline:
        raise SystemExit(f"SSURGO answer not cached ({path}); run once online")
    body = json.dumps({"query": query, "format": "JSON"}).encode()
    err = None
    for k in range(tries):
        try:
            req = urllib.request.Request(SDA, data=body, headers={"Content-Type": "application/json"})
            rows = json.loads(open_url(req, timeout=180).read() or b"{}").get("Table", [])
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(rows))
            return rows
        except Exception as e:  # noqa: BLE001 - network: retry, then give up
            err = e
            time.sleep(2 * (k + 1))
    raise RuntimeError(f"Soil Data Access failed: {err}")


def num(v, nd=1):
    try:
        return round(float(v), nd)
    except (TypeError, ValueError):
        return None


def box_wkt(lat, lon, radius_m):
    """A square of half-width radius_m around a point, as WGS84 WKT."""
    dlat = radius_m / 111320.0
    dlon = radius_m / (111320.0 * math.cos(math.radians(lat)))
    pts = [(lon - dlon, lat - dlat), (lon + dlon, lat - dlat), (lon + dlon, lat + dlat), (lon - dlon, lat + dlat), (lon - dlon, lat - dlat)]
    return "POLYGON((" + ",".join(f"{x:.6f} {y:.6f}" for x, y in pts) + "))"


def mukey_at(lat, lon, offline=False):
    """The map unit under a point: (mukey, musym, muname)."""
    rows = sda(f"""SELECT mu.mukey, mu.musym, mu.muname FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('POINT({lon:.6f} {lat:.6f})') k
JOIN mapunit mu ON mu.mukey=k.mukey""", offline)
    if not rows:
        raise SystemExit(f"no SSURGO map unit at {lat}, {lon}")
    return tuple(rows[0][:3])


def units_in(wkt, offline=False):
    """Map units intersecting a WGS84 polygon with their share of its mapped area: [(mukey, muname, pct)], largest first."""
    rows = sda(f"""~DeclareGeometry(@aoi)~
select @aoi = geometry::STGeomFromText('{wkt}', 4326).MakeValid()
SELECT mu.mukey, mu.muname, SUM(m.mupolygongeo.STIntersection(@aoi).STArea()) AS a
FROM mupolygon m JOIN mapunit mu ON mu.mukey=m.mukey
WHERE m.mupolygongeo.STIntersects(@aoi)=1 GROUP BY mu.mukey, mu.muname""", offline)
    tot = sum(float(r[2]) for r in rows) or 1.0
    return sorted(((str(r[0]), r[1], round(100 * float(r[2]) / tot, 1)) for r in rows), key=lambda t: -t[2])


def layers(mukeys, offline=False):
    """{mukey: {mukey, musym, muname, survey, survey_version, components: [...]}} for the given map units."""
    keys = sorted({str(int(k)) for k in mukeys})
    if not keys:
        return {}
    rows = sda(f"""SELECT mu.mukey, mu.musym, mu.muname, l.areasymbol, l.areaname, sc.saverest,
 c.cokey, c.compname, c.comppct_r, c.majcompflag, c.compkind, c.drainagecl, c.taxclname,
 ch.chkey, ch.hzname, ch.hzdept_r, ch.hzdepb_r, ch.sandtotal_r, ch.silttotal_r, ch.claytotal_r,
 ch.om_r, ch.ph1to1h2o_r, ch.awc_r, ch.ksat_r,
 (SELECT SUM(f.fragvol_r) FROM chfrags f WHERE f.chkey=ch.chkey) AS frag,
 (SELECT TOP 1 t.texdesc FROM chtexturegrp t WHERE t.chkey=ch.chkey AND t.rvindicator='Yes') AS tex
FROM mapunit mu JOIN legend l ON l.lkey=mu.lkey LEFT JOIN sacatalog sc ON sc.areasymbol=l.areasymbol
JOIN component c ON c.mukey=mu.mukey LEFT JOIN chorizon ch ON ch.cokey=c.cokey
WHERE mu.mukey IN ({",".join(keys)})
ORDER BY mu.mukey, c.comppct_r DESC, c.cokey, ch.hzdept_r""", offline)
    return parse_layers(rows)


def parse_layers(rows, keep_keys=False):
    """keep_keys: leave each component's "cokey" and each layer's "chkey" in place (frame mode joins on them)."""
    out = {}
    for r in rows:
        (mukey, musym, muname, area, areaname, saverest, cokey, comp, pct, major, kind, drain, tax,
         chkey, hz, top, bot, sand, silt, clay, om, ph, awc, ksat, frag, tex) = r
        mu = out.setdefault(str(mukey), {"mukey": str(mukey), "musym": musym, "muname": muname,
                                         "survey": f"{areaname} ({area})" if areaname else area,
                                         "survey_version": (saverest or "").split(" ")[0] or None, "components": []})
        comps = mu["components"]
        if not comps or comps[-1]["cokey"] != str(cokey):
            comps.append({"cokey": str(cokey), "name": comp, "pct": num(pct, 0), "major": major == "Yes",
                          "kind": kind, "drainage": drain, "taxonomic_class": tax, "horizons": []})
        if chkey is None or top is None or bot is None:
            continue
        s, si, c = num(sand), num(silt), num(clay)
        comps[-1]["horizons"].append({
            "name": hz, "top_cm": int(float(top)), "bottom_cm": int(float(bot)),
            "sand_pct": s, "silt_pct": si, "clay_pct": c, "om_pct": num(om, 2), "pH": num(ph),
            "awc": num(awc, 2), "ksat_um_s": num(ksat, 2), "rock_frag_pct": num(frag, 0) or 0,
            "texture": (tex or "").lower() or texture_class(s, si, c)})
        if keep_keys:
            comps[-1]["horizons"][-1]["chkey"] = str(chkey)
    if not keep_keys:
        for mu in out.values():
            for c in mu["components"]:
                del c["cokey"]
    return out


def texture_class(sand, silt, clay):
    """USDA soil texture class from sand, silt and clay percent (the texture triangle)."""
    if None in (sand, silt, clay):
        return None
    if silt + 1.5 * clay < 15:
        return "sand"
    if silt + 1.5 * clay < 30:
        return "loamy sand"
    if (7 <= clay < 20 and sand > 52) or (clay < 7 and silt < 50 and silt + 2 * clay >= 30):
        return "sandy loam"
    if 7 <= clay < 27 and 28 <= silt < 50 and sand <= 52:
        return "loam"
    if (silt >= 50 and 12 <= clay < 27) or (50 <= silt < 80 and clay < 12):
        return "silt loam"
    if silt >= 80 and clay < 12:
        return "silt"
    if 20 <= clay < 35 and silt < 28 and sand > 45:
        return "sandy clay loam"
    if 27 <= clay < 40 and 20 < sand <= 45:
        return "clay loam"
    if 27 <= clay < 40 and sand <= 20:
        return "silty clay loam"
    if clay >= 35 and sand > 45:
        return "sandy clay"
    if clay >= 40 and silt >= 40:
        return "silty clay"
    return "clay"


def major(mu):
    """The map unit's largest major component (the soil it is named for), or None."""
    comps = [c for c in mu["components"] if c["horizons"]]
    big = [c for c in comps if c["major"]] or comps
    return max(big, key=lambda c: c["pct"] or 0) if big else None


def summary(comp, n=4):
    """Short layer list for a card: [{top_cm, bottom_cm, texture, clay_pct, sand_pct, rock_frag_pct}]."""
    return [{k: h[k] for k in ("top_cm", "bottom_cm", "texture", "clay_pct", "sand_pct", "rock_frag_pct", "om_pct", "pH")}
            for h in comp["horizons"][:n]]


# ------------------------------------------------------------------ frame mode: map units on the region's grid
FRAME_AREAS = ("CA055", "CA097")      # Napa County, Sonoma County
TILE_DEG = 0.1                        # one Soil Data Access request per 0.1 degree tile (about 100-500 KB of WKT)
SIMPLIFY_DEG = 0.00003                # Douglas-Peucker tolerance on the polygons, about 3 m (the grid is 30 m)
MISC = {"water": "#3d6f8e", "rock outcrop": "#8c8a84", "urban land": "#5b5753", "riverwash": "#d8c99a",
        "pits": "#6e5f52", "dumps": "#6e5f52", "terrace escarpments": "#9b7d5c"}


def tile_query(lon0, lat0, lon1, lat1, areas):
    wkt = f"POLYGON(({lon0:.4f} {lat0:.4f},{lon1:.4f} {lat0:.4f},{lon1:.4f} {lat1:.4f},{lon0:.4f} {lat1:.4f},{lon0:.4f} {lat0:.4f}))"
    return f"""~DeclareGeometry(@aoi)~
select @aoi = geometry::STGeomFromText('{wkt}', 4326)
SELECT m.mukey, m.mupolygongeo.STIntersection(@aoi).Reduce({SIMPLIFY_DEG}).STAsText()
FROM mupolygon m WHERE m.mupolygongeo.STIntersects(@aoi)=1 AND m.areasymbol IN ({",".join(f"'{a}'" for a in areas)})"""


def wkt_rings(wkt):
    """Closed rings of a (MULTI)POLYGON or GEOMETRYCOLLECTION WKT as [(lon, lat), ...]; lines and points are skipped."""
    out = []
    for grp in re.findall(r"\(([^()]+)\)", wkt or ""):
        pts = [tuple(map(float, p.split())) for p in grp.split(",")]
        if len(pts) >= 4 and pts[0] == pts[-1]:
            out.append(pts)
    return out


def fill_feature(grid, rings, val, x0, y1, cell, cols, rows):
    """Set grid cells whose centre lies inside the rings (even-odd, so holes stay open) to val."""
    cross = {}
    for ring in rings:
        for (ax, ay), (bx, by) in zip(ring, ring[1:]):
            if ay == by:
                continue
            lo, hi = (ay, by) if ay < by else (by, ay)
            r0 = max(0, math.ceil((y1 - hi) / cell - 0.5)); r1 = min(rows - 1, math.floor((y1 - lo) / cell - 0.5))
            for r in range(r0, r1 + 1):
                yc = y1 - (r + 0.5) * cell
                if lo <= yc < hi:
                    cross.setdefault(r, []).append(ax + (yc - ay) * (bx - ax) / (by - ay))
    for r, xs in cross.items():
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            c0 = max(0, math.ceil((a - x0) / cell - 0.5)); c1 = min(cols - 1, math.floor((b - x0) / cell - 0.5))
            if c1 >= c0:
                grid[r * cols + c0: r * cols + c1 + 1] = array.array("H", [val]) * (c1 - c0 + 1)


def slope_class(muname):
    m = re.search(r"(\d+) to (\d+) percent slopes", muname or "")
    return f"{m.group(1)} to {m.group(2)} %" if m else None


def series_colors(names):
    """One colour per soil name, largest first: golden-angle hues, earthier (lower saturation) than the geology map's
    palette so the two drapes do not read as the same legend. Water, rock outcrop, urban land and the like keep
    fixed colours."""
    out, k = {}, 0
    for nm in names:
        key = (nm or "").lower()
        fixed = next((c for m, c in MISC.items() if key.startswith(m)), None)
        if fixed:
            out[nm] = fixed
            continue
        r, g, b = colorsys.hls_to_rgb((0.08 + k * 0.381966) % 1.0, (0.46, 0.58, 0.36)[k % 3], (0.40, 0.30, 0.50)[(k // 3) % 3])
        out[nm] = "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))
        k += 1
    return out


def frame_details(mukeys, offline=False):
    """Components and layers of the map units, with each component's slope, restrictive layer and each layer's
    gravel (fragments 2-75 mm) added. Same shape as layers(), keyed by mukey."""
    keys = sorted({str(int(k)) for k in mukeys})
    sql = ",".join(keys)
    rows = sda(f"""SELECT mu.mukey, mu.musym, mu.muname, l.areasymbol, l.areaname, sc.saverest,
 c.cokey, c.compname, c.comppct_r, c.majcompflag, c.compkind, c.drainagecl, c.taxclname,
 ch.chkey, ch.hzname, ch.hzdept_r, ch.hzdepb_r, ch.sandtotal_r, ch.silttotal_r, ch.claytotal_r,
 ch.om_r, ch.ph1to1h2o_r, ch.awc_r, ch.ksat_r,
 (SELECT SUM(f.fragvol_r) FROM chfrags f WHERE f.chkey=ch.chkey) AS frag,
 (SELECT TOP 1 t.texdesc FROM chtexturegrp t WHERE t.chkey=ch.chkey AND t.rvindicator='Yes') AS tex
FROM mapunit mu JOIN legend l ON l.lkey=mu.lkey LEFT JOIN sacatalog sc ON sc.areasymbol=l.areasymbol
JOIN component c ON c.mukey=mu.mukey LEFT JOIN chorizon ch ON ch.cokey=c.cokey
WHERE mu.mukey IN ({sql})
ORDER BY mu.mukey, c.comppct_r DESC, c.cokey, ch.hzdept_r""", offline)
    units = parse_layers(rows, keep_keys=True)
    comp_rows = sda(f"""SELECT c.cokey, c.slope_r,
 (SELECT TOP 1 r.resdept_r FROM corestrictions r WHERE r.cokey=c.cokey AND r.resdept_r IS NOT NULL ORDER BY r.resdept_r) AS rdep,
 (SELECT TOP 1 r.reskind FROM corestrictions r WHERE r.cokey=c.cokey AND r.resdept_r IS NOT NULL ORDER BY r.resdept_r) AS rkind
FROM component c WHERE c.mukey IN ({sql})""", offline)
    gravel_rows = sda(f"""SELECT f.chkey, SUM(f.fragvol_r) FROM chfrags f JOIN chorizon ch ON ch.chkey=f.chkey
JOIN component c ON c.cokey=ch.cokey WHERE c.mukey IN ({sql}) AND COALESCE(f.fragsize_h, f.fragsize_r) <= 76
GROUP BY f.chkey""", offline)
    comp = {str(r[0]): r[1:] for r in comp_rows}
    gravel = {str(r[0]): num(r[1], 0) for r in gravel_rows}
    for mu in units.values():
        for c in mu["components"]:
            slope, rdep, rkind = comp.get(c.pop("cokey"), (None, None, None))
            c["slope_pct"] = num(slope, 0)
            c["restriction"] = {"depth_cm": int(float(rdep)), "kind": rkind} if rdep is not None else None
            for h in c["horizons"]:
                h["gravel_pct"] = gravel.get(h.pop("chkey")) or 0
    return units


def frame_grid(region):
    x0, y0, x1, y1 = region["bbox_utm"]
    cell = region.get("cell_m", 30)
    return x0, y0, x1, y1, cell, round((x1 - x0) / cell), round((y1 - y0) / cell)


def build_frame(region_path, areas=FRAME_AREAS, offline=False):
    from fetch_terrain import utm_from_geographic
    from fetch_tiles import geographic_from_utm
    region = json.loads(Path(region_path).read_text())
    x0, y0, x1, y1, cell, cols, rows = frame_grid(region)
    corners = [geographic_from_utm(e, n) for e in (x0, x1) for n in (y0, y1)]
    la0, la1 = min(c[0] for c in corners), max(c[0] for c in corners)
    lo0, lo1 = min(c[1] for c in corners), max(c[1] for c in corners)
    grid = array.array("H", bytes(2 * cols * rows))
    index = {}
    lat = math.floor(la0 / TILE_DEG) * TILE_DEG
    ntiles = 0
    while lat < la1:
        lon = math.floor(lo0 / TILE_DEG) * TILE_DEG
        while lon < lo1:
            for mukey, wkt in sda(tile_query(lon, lat, lon + TILE_DEG, lat + TILE_DEG, areas), offline):
                rings = [[utm_from_geographic(y, x) for x, y in ring] for ring in wkt_rings(wkt)]
                if rings:
                    val = index.setdefault(str(mukey), len(index) + 1)
                    fill_feature(grid, rings, val, x0, y1, cell, cols, rows)
            lon += TILE_DEG; ntiles += 1
        lat += TILE_DEG
    if len(index) > 65535:
        raise SystemExit("more map units than the 16-bit grid holds")
    counts = [0] * (len(index) + 1)
    for v in grid:
        counts[v] += 1
    covered = sum(counts[1:])
    details = frame_details(index, offline)
    # units in order of area, largest first; the grid is renumbered to match
    order = sorted((k for k in index if counts[index[k]] > 0 and k in details), key=lambda k: -counts[index[k]])
    renum = [0] * (len(index) + 1)
    for i, k in enumerate(order):
        renum[index[k]] = i + 1
    series_area = {}
    for k in order:
        m = major(details[k]) or (details[k]["components"] or [{"name": details[k]["muname"]}])[0]
        series_area[m["name"]] = series_area.get(m["name"], 0) + counts[index[k]]
    names = sorted(series_area, key=lambda s: -series_area[s])
    colors = series_colors(names)
    units, surveys = [], {}
    for k in order:
        mu = details[k]
        m = major(mu) or (mu["components"] or [{"name": mu["muname"]}])[0]
        area = mu["survey"].rsplit("(", 1)[-1].rstrip(")")
        surveys[area] = {"areasymbol": area, "name": mu["survey"].rsplit(" (", 1)[0], "version": mu["survey_version"]}
        units.append({"mukey": k, "musym": mu["musym"], "name": mu["muname"], "slope_class": slope_class(mu["muname"]),
                      "survey": area, "series": names.index(m["name"]), "area_pct": round(100 * counts[index[k]] / covered, 2),
                      "components": [{kk: c[kk] for kk in ("name", "pct", "major", "kind", "drainage", "slope_pct", "restriction")}
                                     | {"horizons": [{kk: h[kk] for kk in ("name", "top_cm", "bottom_cm", "texture", "sand_pct", "silt_pct",
                                                                            "clay_pct", "gravel_pct", "rock_frag_pct", "om_pct", "pH", "awc")}
                                                     for h in c["horizons"]]}
                                     for c in mu["components"]]})
    out_dir = ROOT / region["assets_dir"]
    rgba = bytearray(4 * cols * rows)
    for i, v in enumerate(grid):
        if v:
            n = renum[v]
            if n:
                rgba[4 * i] = n >> 8; rgba[4 * i + 1] = n & 255; rgba[4 * i + 3] = 255
    write_png(out_dir / "soils.png", rgba, cols, rows)
    meta = {
        "label": "USDA SSURGO 1:24,000",
        "source": SOURCE, "rights": "USDA-NRCS, US public domain (SOURCES.md G44)",
        "note": "Map unit averages: each map unit lists the soils (components) it is made of and the survey's representative "
                "layer values for each. Not a soil pit at any one spot. Survey scale about 1:24,000.",
        "surveys": sorted(surveys.values(), key=lambda s: s["areasymbol"]), "queried": time.strftime("%Y-%m-%d"),
        "grid": {"file": "soils.png", "bbox_utm": [x0, y0, x1, y1], "cell_m": cell, "cols": cols, "rows": rows,
                 "encoding": "row 0 north; red*256+green = 1 + index into units; alpha 0 = no map unit from these surveys",
                 "covered_pct": round(100 * covered / (cols * rows), 1), "tiles": ntiles},
        "series": [{"name": s, "color": colors[s], "area_pct": round(100 * series_area[s] / covered, 2)} for s in names],
        "units": units,
    }
    (out_dir / "soils.json").write_text(json.dumps(meta, separators=(",", ":")) + "\n")
    return meta


def write_png(path, rgba, w, h):
    raw = b"".join(b"\x00" + bytes(rgba[r * w * 4:(r + 1) * w * 4]) for r in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)  # noqa: E731
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--point", nargs=2, type=float, metavar=("LAT", "LON"))
    ap.add_argument("--radius", type=float, default=150, help="also list map units within this half-width (m)")
    ap.add_argument("--frame", metavar="REGION_JSON", help="build soils.png and soils.json for a region frame")
    ap.add_argument("--areas", nargs="+", default=list(FRAME_AREAS), help="survey areas for --frame")
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    if a.frame:
        m = build_frame(a.frame, a.areas, a.offline)
        print(f"{len(m['units'])} map units, {len(m['series'])} soil names, {m['grid']['covered_pct']} % of the frame covered")
        return
    if not a.point:
        ap.error("give --point or --frame")
    lat, lon = a.point
    mukey, musym, muname = mukey_at(lat, lon, a.offline)
    print(f"map unit {musym} {muname} (mukey {mukey})")
    for k, nm, p in units_in(box_wkt(lat, lon, a.radius), a.offline):
        print(f"  within {a.radius:.0f} m: {p:5.1f} %  {nm}")
    mu = layers([mukey], a.offline)[mukey]
    for c in mu["components"]:
        print(f"  {c['pct']:3.0f} % {c['name']} ({c['drainage'] or 'drainage not given'})")
        for h in c["horizons"]:
            print(f"      {h['name']:5} {h['top_cm']:3}-{h['bottom_cm']:<3} cm {h['texture']:22} sand {h['sand_pct']} silt {h['silt_pct']} "
                  f"clay {h['clay_pct']} OM {h['om_pct']} pH {h['pH']} rock {h['rock_frag_pct']} %")


if __name__ == "__main__":
    main()
