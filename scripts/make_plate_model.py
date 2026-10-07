#!/usr/bin/env python3
"""Real continent motion for the globe, 410 Ma to today, from the Müller et al. (2019) plate model.

Tier 0, standard library only (no pyGPlates). Input: a checkout of GPlates/pygplates-tutorials (GitHub,
CC BY 3.0, EarthByte Group), which carries the model's two rotation files and its present-day coastline
polygons:
  data/Muller_etal_2019_PlateMotionModel_v2.0_Tectonics/Global_250-0Ma_Rotations_2019_v2.rot
  data/Muller_etal_2019_PlateMotionModel_v2.0_Tectonics/Global_410-250Ma_Rotations_2019_v2.rot
  data/Muller_etal_2019_PlateMotionModel_v2.0_Tectonics/StaticGeometries/Coastlines/Global_coastlines_2019_v1_low_res.*

What it does, as GPlates does it:
  1. Each rotation line is a finite rotation (Euler pole latitude, longitude, angle) of a moving plate relative to
     a fixed plate at an age. Between two lines of the same moving/fixed pair the rotation is interpolated
     (quaternion slerp).
  2. A plate's absolute rotation at an age is the chain of relative rotations down to plate 000 (the model's
     mantle reference frame), composed.
  3. Each coastline polygon belongs to one plate (PLATEID1) and exists between FROMAGE and TOAGE; rotating its
     present-day vertices by its plate's absolute rotation puts it where it was.
The viewer does step 3 itself, so this script only writes the polygons (present-day, simplified) and each plate's
absolute rotation every --step Ma, which the viewer interpolates in between.

Output: prototype/assets/plates/muller2019.json
  {"source", "rights", "ages": [0, step, ...], "plates": [plate ids],
   "quats": [per plate: [w, x, y, z] for each age, flattened, 5 decimals],
   "polys": [[plate index, from_age, to_age, lat0, lon0, dlat1, dlon1, ...] (0.01 degree units)], "anchor": 0}
Quaternions rotate unit vectors x = cos(lat)cos(lon), y = cos(lat)sin(lon), z = sin(lat) (Earth-centred).

Rights: EarthByte Group, CC BY 3.0 Unported (repository LICENSE.md). Cite Müller, R. D., et al. (2019), A global
plate model including lithospheric deformation along major rifts and orogens since the Triassic, Tectonics
38, 1884-1907, doi:10.1029/2018TC005462; 410-250 Ma rotations from Young et al. (2019), Geoscience Frontiers
10, 989-1013, doi:10.1016/j.gsf.2018.05.011. SOURCES.md G32.

Usage: make_plate_model.py --src <pygplates-tutorials checkout> [--step 5] [--max-age 410] [--tolerance 0.2]
"""
import argparse
import datetime
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_rivers import read_dbf  # noqa: E402

MODEL = Path("data/Muller_etal_2019_PlateMotionModel_v2.0_Tectonics")
ROT_FILES = ["Global_250-0Ma_Rotations_2019_v2.rot", "Global_410-250Ma_Rotations_2019_v2.rot"]
COAST = "StaticGeometries/Coastlines/Global_coastlines_2019_v1_low_res"
SOURCE = ("Müller et al. (2019) plate motion model v2.0 (Tectonics, doi:10.1029/2018TC005462), 250-0 Ma, and "
          "Young et al. (2019) (Geoscience Frontiers, doi:10.1016/j.gsf.2018.05.011) 410-250 Ma rotations, as "
          "distributed in GPlates/pygplates-tutorials (EarthByte Group)")
RIGHTS = "CC BY 3.0 Unported, EarthByte Group (pygplates-tutorials LICENSE.md). Credit the EarthByte Group and cite Müller et al. 2019."


# ---------------------------------------------------------------- quaternions (w, x, y, z)
def q_pole(lat, lon, angle):
    la, lo, h = math.radians(lat), math.radians(lon), math.radians(angle) / 2
    s = math.sin(h)
    return (math.cos(h), math.cos(la) * math.cos(lo) * s, math.cos(la) * math.sin(lo) * s, math.sin(la) * s)


def q_mul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz, aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw)


def q_slerp(a, b, t):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0:
        b, d = tuple(-x for x in b), -d
    if d > 0.9995:
        r = tuple(x + t * (y - x) for x, y in zip(a, b))
    else:
        th = math.acos(d)
        s0, s1 = math.sin((1 - t) * th) / math.sin(th), math.sin(t * th) / math.sin(th)
        r = tuple(s0 * x + s1 * y for x, y in zip(a, b))
    n = math.sqrt(sum(x * x for x in r))
    return tuple(x / n for x in r)


def q_rotate(q, v):
    w, x, y, z = q
    p = q_mul(q_mul(q, (0.0,) + tuple(v)), (w, -x, -y, -z))
    return p[1:]


# ---------------------------------------------------------------- rotation model
def read_rotations(paths):
    """{moving plate: [sequence, ...]}; a sequence is a fixed plate and its [(age, quaternion), ...] in age order."""
    seqs = {}
    for path in paths:
        last = None
        for line in Path(path).read_text(encoding="latin-1").splitlines():
            parts = line.split("!")[0].split()
            if len(parts) < 6:
                continue
            mov, age, lat, lon, ang, fix = int(parts[0]), float(parts[1]), *map(float, parts[2:5]), int(parts[5])
            if mov == 999 or mov == fix:
                continue
            q = q_pole(lat, lon, ang)
            if last and last[0] == mov and last[1] == fix:
                last[2].append((age, q))
            else:
                last = (mov, fix, [(age, q)])
                seqs.setdefault(mov, []).append(last)
    return seqs


class Model:
    def __init__(self, seqs):
        self.seqs = seqs
        self.cache = {}

    def relative(self, plate, age):
        """(fixed plate, quaternion) for plate at age, or None if the model has no rotation for it then."""
        for _, fix, pts in self.seqs.get(plate, []):
            if pts[0][0] <= age <= pts[-1][0]:
                for (a0, q0), (a1, q1) in zip(pts, pts[1:]):
                    if a0 <= age <= a1:
                        return fix, (q0 if a1 == a0 else q_slerp(q0, q1, (age - a0) / (a1 - a0)))
                return fix, pts[0][1]
        return None

    def absolute(self, plate, age, depth=0):
        key = (plate, age)
        if plate == 0:
            return (1.0, 0.0, 0.0, 0.0)
        if key in self.cache:
            return self.cache[key]
        if depth > 60:
            raise SystemExit(f"rotation chain too deep for plate {plate} at {age} Ma (cycle?)")
        rel = self.relative(plate, age)
        q = None if rel is None else (lambda f: None if f is None else q_mul(f, rel[1]))(self.absolute(rel[0], age, depth + 1))
        self.cache[key] = q
        return q


# ---------------------------------------------------------------- coastlines
def read_polygons(data):
    """Rings of each record of a Polygon shapefile, as lists of (lon, lat)."""
    if struct.unpack("<i", data[32:36])[0] not in (5, 15, 25):
        raise SystemExit("not a polygon shapefile")
    out, pos = [], 100
    while pos < len(data):
        _, clen = struct.unpack(">ii", data[pos:pos + 8])
        body = data[pos + 8: pos + 8 + clen * 2]
        pos += 8 + clen * 2
        if struct.unpack("<i", body[:4])[0] == 0:
            out.append([])
            continue
        nparts, npts = struct.unpack("<ii", body[36:44])
        starts = list(struct.unpack(f"<{nparts}i", body[44:44 + 4 * nparts])) + [npts]
        xy = struct.unpack(f"<{2 * npts}d", body[44 + 4 * nparts: 44 + 4 * nparts + 16 * npts])
        out.append([[(xy[2 * k], xy[2 * k + 1]) for k in range(starts[j], starts[j + 1])] for j in range(nparts)])
    return out


def xyz(lon, lat):
    la, lo = math.radians(lat), math.radians(lon)
    return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))


def simplify_sphere(pts, tol_deg):
    """Douglas-Peucker on the sphere (distance to the great circle through the end points), open line."""
    if len(pts) < 3:
        return pts
    tol = math.radians(tol_deg)
    v = [xyz(*p) for p in pts]
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        a, b = v[i], v[j]
        n = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
        nn = math.sqrt(sum(c * c for c in n))
        best, k = -1.0, -1
        for m in range(i + 1, j):
            d = abs(sum(x * y for x, y in zip(n, v[m]))) / nn if nn > 1e-12 else math.acos(max(-1, min(1, sum(x * y for x, y in zip(a, v[m])))))
            if d > best:
                best, k = d, m
        if best > tol:
            keep[k] = True
            stack += [(i, k), (k, j)]
    return [p for p, f in zip(pts, keep) if f]


def ring_area_deg2(ring):
    """Rough planar area in square degrees (cos-lat scaled), to drop specks."""
    if len(ring) < 3:
        return 0.0
    lat0 = sum(p[1] for p in ring) / len(ring)
    c = math.cos(math.radians(lat0))
    return abs(sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
                   for i in range(len(ring) - 1))) / 2 * c


def build(src, step=5, max_age=410, tolerance=0.2, min_area=0.05):
    base = Path(src) / MODEL
    model = Model(read_rotations([base / f for f in ROT_FILES]))
    shp = (base / (COAST + ".shp")).read_bytes()
    dbf = (base / (COAST + ".dbf")).read_bytes()
    recs = read_dbf(dbf)
    geoms = read_polygons(shp)
    ages = list(range(0, max_age + 1, step))
    plates, polys, dropped = [], [], {"no_rotation": 0, "tiny": 0}
    for rec, rings in zip(recs, geoms):
        if not rec or not rings:
            continue
        pid = int(rec["PLATEID1"] or 0)
        frm = float(rec["FROMAGE"] if rec["FROMAGE"] is not None else 600)
        to = float(rec["TOAGE"] if rec["TOAGE"] is not None else -999)
        to = max(to, 0.0)
        if to > max_age:
            continue
        if model.absolute(pid, 0.0) is None:
            dropped["no_rotation"] += 1
            continue
        for ring in rings[:1]:                       # outer ring only: coastline holes are lakes, left out
            if ring_area_deg2(ring) < min_area:
                dropped["tiny"] += 1
                continue
            h = len(ring) // 2
            r = simplify_sphere(ring[:h + 1], tolerance)[:-1] + simplify_sphere(ring[h:], tolerance)
            if r[0] == r[-1]:
                r = r[:-1]
            if len(r) < 3:
                dropped["tiny"] += 1
                continue
            if pid not in plates:
                plates.append(pid)
            row = [plates.index(pid), round(min(frm, 9999)), round(to)]
            plat = plon = 0
            for lon, lat in r:
                ilat, ilon = round(lat * 100), round(lon * 100)
                row += [ilat - plat, ilon - plon]
                plat, plon = ilat, ilon
            polys.append(row)
    quats, gaps = [], 0
    for pid in plates:
        last = (1.0, 0.0, 0.0, 0.0)
        for a in ages:
            q = model.absolute(pid, float(a))
            if q is None:                              # outside the plate's rotation record: hold the last pose
                q, gaps = last, gaps + 1
            if q[0] < 0:
                q = tuple(-c for c in q)
            quats += [round(c, 4) for c in q]
            last = q
    files = {f: hashlib.sha256((base / f).read_bytes()).hexdigest() for f in ROT_FILES}
    files.update({COAST + ext: hashlib.sha256((base / (COAST + ext)).read_bytes()).hexdigest() for ext in (".shp", ".dbf")})
    doc = {"source": SOURCE, "rights": RIGHTS, "built": datetime.date.today().isoformat(), "anchor": 0,
           "ages": ages, "plates": plates, "quats": quats, "polys": polys,
           "format": "polys: [plate index, from_age, to_age, lat0, lon0, dlat, dlon, ...] in 0.01 degrees, "
                     "present-day positions; quats: per plate, [w, x, y, z] at each of ages",
           "limits": f"Coastlines simplified to about {tolerance} degrees; outer rings only. Continents only, no "
                     "plate boundaries or ocean floor. The 410-250 Ma rotations are older and less certain than "
                     "the 250-0 Ma part. Longitude before ~200 Ma is weakly constrained in any model.",
           "files": files, "dropped": dropped, "held_poses": gaps}
    out = ROOT / "prototype" / "assets" / "plates" / "muller2019.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, separators=(",", ":")) + "\n")
    return doc, out, model


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--step", type=int, default=5)
    ap.add_argument("--max-age", type=int, default=410)
    ap.add_argument("--tolerance", type=float, default=0.2)
    a = ap.parse_args()
    doc, out, _ = build(a.src, a.step, a.max_age, a.tolerance)
    nv = sum((len(p) - 3) // 2 for p in doc["polys"])
    print(f"{out.relative_to(ROOT)}: {len(doc['polys'])} polygons, {nv} vertices, {len(doc['plates'])} plates, "
          f"{len(doc['ages'])} ages; dropped {doc['dropped']}; held poses {doc['held_poses']}; "
          f"{out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
