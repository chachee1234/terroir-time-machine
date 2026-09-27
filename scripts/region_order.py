#!/usr/bin/env python3
"""Order in which new wine regions are added (owner rule, 2026-09-27).

Start with Sonoma Valley. Then branch out to the AVA next door: an unmapped region whose boundary
touches (comes within --touch-km of) a region already mapped, nearest to the one mapped last. When
nothing touches, move to the closest unmapped region anywhere.

What counts as a region ("frame"): a current California AVA small enough for one 3D block (bounding
box at most --max-km on each side). Bigger umbrella AVAs (North Coast, Sonoma Coast, Central Coast,
Sierra Foothills...) are covered piece by piece by the frames inside them. An AVA nested inside a
mapped frame (UC Davis `within` field) becomes a close-up of that frame, not a region of its own.

Tier 0, stdlib only. Input: prototype/assets/globe/ca_avas.json (UC Davis AVA Project, CC0, built by
build_globe.py). Output: prototype/assets/regions/order.json (the viewer colours the globe with it), and the list on stdout.

Usage: region_order.py [--start sonoma_valley] [--mapped napa_valley] [--limit 40]
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AVAS = ROOT / "prototype" / "assets" / "globe" / "ca_avas.json"
OUT = ROOT / "prototype" / "assets" / "regions" / "order.json"   # read by the viewer
KX = 111.32 * math.cos(math.radians(37))   # km per degree of longitude near California's middle
KY = 110.57


def xy(p):
    return (p[0] * KX, p[1] * KY)


def load(path=AVAS):
    out = {}
    for a in json.loads(Path(path).read_text())["avas"]:
        pts = [xy(p) for r in a["rings"] for p in r]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        big = max(a["rings"], key=len)
        out[a["id"]] = {"id": a["id"], "name": a["name"], "pts": pts, "bb": (min(xs), min(ys), max(xs), max(ys)),
                        "c": centroid([xy(p) for p in big]),
                        "within": {w.strip() for w in (a.get("within") or "").split("|") if w.strip()}}
    return out


def centroid(ring):
    A = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        f = x0 * y1 - x1 * y0
        A += f; cx += (x0 + x1) * f; cy += (y0 + y1) * f
    if abs(A) < 1e-9:
        return ring[0]
    return (cx / (3 * A), cy / (3 * A))


def size_km(a):
    b = a["bb"]
    return max(b[2] - b[0], b[3] - b[1])


def gap_km(a, b, cap=1e9):
    """Smallest vertex-to-vertex distance between two AVAs (0 if one contains the other's centroid box)."""
    A, B = a["bb"], b["bb"]
    dx = max(0.0, max(A[0], B[0]) - min(A[2], B[2]))
    dy = max(0.0, max(A[1], B[1]) - min(A[3], B[3]))
    box = math.hypot(dx, dy)
    if box > cap:
        return box
    if B[0] <= a["c"][0] <= B[2] and B[1] <= a["c"][1] <= B[3] and inside(a["c"], b["pts"]):
        return 0.0
    cell = max(cap, 2.0)
    grid = {}
    for p in b["pts"]:
        grid.setdefault((int(p[0] // cell), int(p[1] // cell)), []).append(p)
    best = 1e9
    for p in a["pts"]:
        gx, gy = int(p[0] // cell), int(p[1] // cell)
        for i in (gx - 1, gx, gx + 1):
            for j in (gy - 1, gy, gy + 1):
                for q in grid.get((i, j), ()):
                    d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
                    if d < best:
                        best = d
    return math.sqrt(best) if best < 1e9 else max(box, cell)


def inside(pt, poly):
    x, y, c = pt[0], pt[1], False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def order(avas, start="sonoma_valley", mapped=("napa_valley",), max_km=80.0, touch_km=1.5, limit=40):
    frames = {k for k, a in avas.items() if size_km(a) <= max_km}
    done, seq, names = list(mapped), [], {avas[k]["name"] for k in mapped if k in avas}

    def covered(k):
        """Inside a mapped region, directly or through AVAs nested in it."""
        cov, grow = set(names), True
        while grow:
            new = {a["name"] for a in avas.values() if a["within"] & cov} - cov
            cov |= new; grow = bool(new)
        return avas[k]["name"] in cov and k not in done

    def take(k, why, gap):
        seq.append({"id": k, "name": avas[k]["name"], "rule": why, "gap_km": round(gap, 1),
                    "size_km": round(size_km(avas[k]), 1),
                    "close_ups": sorted(o for o in avas if avas[avas[o]["id"]]["within"] & {avas[k]["name"]} and o not in done)})
        done.append(k); names.add(avas[k]["name"])

    byname = {avas[k]["name"]: k for k in frames}

    def parent(k):
        """Map a region's frame-sized parent AVA first, so the region becomes one of its close-ups."""
        ps = [byname[w] for w in avas[k]["within"] if w in byname and byname[w] not in done and not covered(byname[w])]
        return min(ps, key=lambda q: size_km(avas[q])) if ps else k

    if start in avas:
        take(start, "owner's choice", 0.0)
    while len(seq) < limit:
        todo = [k for k in frames if k not in done and not covered(k)]
        if not todo:
            break
        last = avas[done[-1]]
        touching = [(math.dist(avas[k]["c"], last["c"]), k) for k in todo
                    if min(gap_km(avas[k], avas[m], touch_km) for m in done) <= touch_km]
        if touching:
            d, k = min(touching)
            q = parent(k)
            take(q, "touches a mapped region" if q == k else f"parent of {avas[k]['name']}, which touches a mapped region", 0.0)
            continue
        g, k = min((min(gap_km(avas[k], avas[m], 200.0) for m in done), k) for k in todo)
        q = parent(k)
        take(q, "closest (nothing touching)" if q == k else f"parent of {avas[k]['name']}, the closest", g)
    return seq


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="sonoma_valley")
    ap.add_argument("--mapped", default="napa_valley", help="comma-separated AVA ids already mapped")
    ap.add_argument("--max-km", type=float, default=80.0)
    ap.add_argument("--touch-km", type=float, default=1.5)
    ap.add_argument("--limit", type=int, default=40)
    a = ap.parse_args()
    seq = order(load(), a.start, [m for m in a.mapped.split(",") if m], a.max_km, a.touch_km, a.limit)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"rule": "start with --start; then the unmapped region touching a mapped one, nearest to the last mapped; "
                                       "when none touches, the closest unmapped region",
                               "source": "prototype/assets/globe/ca_avas.json (UC Davis AVA Project, CC0)",
                               "params": vars(a), "order": seq}, indent=1) + "\n")
    for i, s in enumerate(seq, 1):
        print(f"{i:2d}. {s['name']:<32} {s['rule']:<28} {s['size_km']:5.1f} km  close-ups: {len(s['close_ups'])}")


if __name__ == "__main__":
    main()
