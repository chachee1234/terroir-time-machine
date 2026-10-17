#!/usr/bin/env python3
"""G1: resolved plate boundaries (ridges, trenches, transforms) every 1 Myr, 0–410 Ma, from the Müller et al. (2019)
plate model, for the globe's plate colours and boundary lines.

Needs pyGPlates (the owner's Mac; not installed in the cloud sandbox). Run it there with the model's rotation files
and topology files (see SOURCES.md G32 and the G1 status note for the exact download names):

  python3 scripts/export_plate_topologies.py \
      --rotations <dir>/Global_250-0Ma_Rotations_2019_v2.rot <dir>/Global_410-250Ma_Rotations_2019_v2.rot \
      --topologies <dir>/<topology .gpml files from the same model> \
      --max-age 410 --step 1 --out prototype/assets/plates/topologies.json

How it works, as GPlates does it: each topology feature is reconstructed to every age with pygplates.reconstruct
(anchor plate 0). Its line geometry is kept only where the feature exists at that age. Points are quantised to
0.01 degree so the file stays small; each boundary carries its feature type (MidOceanRidge, SubductionZone,
Transform, ...), so the viewer can draw teeth on trenches and arrows on transforms.

Output (one file, every age from 0 to --max-age in --step Ma):
  {"source", "rights", "ages": [...], "units": "0.01 degree lat, lon",
   "frames": [ per age: [ [type_index, [lat0, lon0, dlat1, dlon1, ...]], ... ] ],
   "types": [feature type names]}
Rights: EarthByte Group, CC BY 3.0 (the model's licence); cite Müller et al. (2019), doi:10.1029/2018TC005462.

Pure helpers (quantise, frame encoding, size report) are importable without pygplates, so they can be tested in the
sandbox; only run_export() needs pygplates.
"""
import argparse
import json
import sys
from pathlib import Path

BOUNDARY_TYPES = {  # GPML feature types drawn on the globe; anything else is skipped
    "MidOceanRidge", "SubductionZone", "Transform", "ContinentalRift", "Unclassified", "OceanicBasin",
}
ROOT = Path(__file__).resolve().parent.parent


def quantise(lat, lon):
    """Degrees to integers in 0.01 degree units, lon wrapped to [-180, 180)."""
    lon = (lon + 180.0) % 360.0 - 180.0
    return int(round(lat * 100)), int(round(lon * 100))


def encode_line(points):
    """A polyline of (lat, lon) degrees as [lat0, lon0, dlat1, dlon1, ...] deltas, 0.01 degree units.

    Consecutive duplicate points are dropped, so stationary parts of a boundary cost nothing.
    """
    out, last = [], None
    for lat, lon in points:
        q = quantise(lat, lon)
        if last is None:
            out += [q[0], q[1]]
        elif q != last:
            out += [q[0] - last[0], q[1] - last[1]]
        else:
            continue
        last = q
    return out


def frame_size_bytes(frame):
    """Size of a frame as written: compact JSON, used to check the globe's 6 MB budget."""
    return len(json.dumps(frame, separators=(",", ":")).encode())


def run_export(rotation_files, topology_files, max_age, step):  # pragma: no cover - needs pygplates on the owner's Mac
    import pygplates  # noqa: PLC0415 - optional dependency, imported only for the real run

    rotations = pygplates.RotationModel([str(p) for p in rotation_files])
    features = []
    for path in topology_files:
        features += list(pygplates.FeatureCollection(str(path)))
    ages = list(range(0, max_age + 1, step))
    types = sorted(BOUNDARY_TYPES)
    frames = []
    for age in ages:
        frame = []
        for feat in features:
            ftype = feat.get_feature_type().get_name()
            if ftype not in BOUNDARY_TYPES or not feat.get_geometry():
                continue
            for rfg in pygplates.reconstruct(feat, rotations, age, anchor_plate_id=0):
                geom = rfg.get_reconstructed_geometry()
                if geom is None:
                    continue
                pts = [p.to_lat_lon() for p in geom.get_points()] if hasattr(geom, "get_points") else []
                if len(pts) >= 2:
                    frame.append([types.index(ftype), encode_line(pts)])
        frames.append(frame)
    return ages, types, frames


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--rotations", nargs="+", required=True)
    ap.add_argument("--topologies", nargs="+", required=True)
    ap.add_argument("--max-age", type=int, default=410)
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--out", default=str(ROOT / "prototype/assets/plates/topologies.json"))
    args = ap.parse_args(argv)
    ages, types, frames = run_export(args.rotations, args.topologies, args.max_age, args.step)
    doc = {
        "source": "Müller, R. D., et al. (2019), Tectonics 38, 1884-1907, doi:10.1029/2018TC005462 "
                  "(topologies exported with pyGPlates)",
        "rights": "EarthByte Group, CC BY 3.0 Unported; credit Müller et al. (2019)",
        "ages": ages, "units": "0.01 degree lat, lon; first point absolute, then deltas",
        "types": types, "frames": frames,
    }
    total = sum(frame_size_bytes(f) for f in frames)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(doc, separators=(",", ":")))
    print(f"wrote {args.out}: {len(ages)} ages, {total / 1e6:.2f} MB of frames")
    if total > 6_000_000:
        print("WARNING: over the 6 MB globe budget (AUTOPILOT G0 rule); raise --step or simplify", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
