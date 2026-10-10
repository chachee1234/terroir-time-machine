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

Answers are cached in data/raw/ssurgo/ (git-ignored), so a rebuild works offline once fetched.
"""
import argparse
import hashlib
import json
import math
import sys
import time
import urllib.request
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


def parse_layers(rows):
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--point", nargs=2, type=float, metavar=("LAT", "LON"), required=True)
    ap.add_argument("--radius", type=float, default=150, help="also list map units within this half-width (m)")
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
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
