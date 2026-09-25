"""Tier 0 validator for SCENES.json.

Implements the GOVERNANCE.md §3 validation checks (schema, age-range sanity,
license ledger, cross-reference integrity) using the semantic rules listed in
SCENES_README.md. Standard library only; full JSON Schema validation runs when
the optional `jsonschema` package is installed and is reported as skipped otherwise.

Usage: python3 scripts/validate.py [path/to/SCENES.json]
Exit code 1 if any error is found; warnings do not fail.
"""

import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER_ID = re.compile(r"^\|\s*([A-Za-z][A-Za-z0-9_-]*)\s*\|", re.MULTILINE)


def ledger_ids(sources_md_text):
    """Source IDs registered in the first column of SOURCES.md tables."""
    return {m for m in LEDGER_ID.findall(sources_md_text) if m not in ("ID", "Check")}


def _interval(obj):
    time = obj.get("time") or {}
    return time.get("older_ma"), time.get("younger_ma")


def _check_unique(items, table, errors):
    seen = set()
    for item in items:
        item_id = item.get("id")
        if item_id in seen:
            errors.append(f"{table}: duplicate id '{item_id}'")
        seen.add(item_id)
    return seen


def _check_refs(ids, known, where, kind, errors):
    for ref in ids or []:
        if ref not in known:
            errors.append(f"{where}: unknown {kind} '{ref}'")


def validate(manifest, root=ROOT, registered_ids=None):
    """Return (errors, warnings) for a parsed SCENES.json manifest."""
    errors, warnings = [], []
    sources = manifest.get("sources", [])
    claims = manifest.get("claims", [])
    assets = manifest.get("assets", [])
    scenes = manifest.get("scenes", [])

    source_ids = _check_unique(sources, "sources", errors)
    claim_ids = _check_unique(claims, "claims", errors)
    asset_ids = _check_unique(assets, "assets", errors)
    _check_unique(scenes, "scenes", errors)

    # Age-range sanity
    for table, items in (("claims", claims), ("scenes", scenes)):
        for item in items:
            older, younger = _interval(item)
            if older is not None and younger is not None and older < younger:
                errors.append(f"{table} '{item.get('id')}': older_ma {older} < younger_ma {younger}")

    previous_older = None
    for scene in scenes:
        sid = scene.get("id")
        older, younger = _interval(scene)
        if previous_older is not None and older is not None and older > previous_older:
            errors.append(f"scene '{sid}': scenes not ordered oldest to youngest")
        previous_older = older

        previous_age = None
        for frame in scene.get("keyframes") or []:
            age = frame.get("age_ma")
            if age is None:
                continue
            if older is not None and younger is not None and not younger <= age <= older:
                errors.append(f"scene '{sid}': keyframe at {age} Ma outside scene interval {older}-{younger} Ma")
            if previous_age is not None and age > previous_age:
                errors.append(f"scene '{sid}': keyframes not ordered oldest to youngest")
            previous_age = age
            _check_refs(frame.get("asset_ids"), set(scene.get("asset_ids") or []),
                        f"scene '{sid}' keyframe {age} Ma", "scene asset", errors)

    # Cross-reference integrity
    for scene in scenes:
        where = f"scene '{scene.get('id')}'"
        _check_refs(scene.get("claim_ids"), claim_ids, where, "claim", errors)
        _check_refs(scene.get("asset_ids"), asset_ids, where, "asset", errors)
        model = scene.get("model") or {}
        _check_refs(model.get("source_ids"), source_ids, f"{where} model", "source", errors)
        anchor = scene.get("local_anchor") or {}
        if anchor.get("place_source_id"):
            _check_refs([anchor["place_source_id"]], source_ids, f"{where} anchor", "source", errors)

    for claim in claims:
        refs = [e.get("source_id") for e in claim.get("evidence") or []]
        _check_refs(refs, source_ids, f"claim '{claim.get('id')}'", "source", errors)

    for asset in assets:
        where = f"asset '{asset.get('id')}'"
        _check_refs(asset.get("claim_ids"), claim_ids, where, "claim", errors)
        _check_refs(asset.get("source_ids"), source_ids, where, "source", errors)
        path = asset.get("path")
        if not path:
            continue
        full = os.path.join(root, path)
        if not os.path.isfile(full):
            errors.append(f"{where}: file not found '{path}'")
            continue
        with open(full, "rb") as fh:
            data = fh.read()
        if asset.get("bytes") is not None and len(data) != asset["bytes"]:
            errors.append(f"{where}: size {len(data)} != declared {asset['bytes']}")
        if asset.get("sha256") and hashlib.sha256(data).hexdigest() != asset["sha256"]:
            errors.append(f"{where}: sha256 mismatch")

    # License ledger
    if registered_ids is not None:
        for sid in sorted(source_ids):
            if sid not in registered_ids:
                warnings.append(f"source '{sid}': no entry in SOURCES.md")

    return errors, warnings


def schema_errors(manifest, schema_path):
    """Full JSON Schema check if jsonschema is available; None if skipped."""
    try:
        import jsonschema
    except ImportError:
        return None
    with open(schema_path) as fh:
        schema = json.load(fh)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    return [f"schema: {'/'.join(map(str, e.path)) or '<root>'}: {e.message}"
            for e in validator.iter_errors(manifest)]


def main(argv):
    manifest_path = argv[1] if len(argv) > 1 else os.path.join(ROOT, "SCENES.json")
    try:
        with open(manifest_path) as fh:
            manifest = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {manifest_path}: {exc}")
        return 1

    registered = None
    sources_md = os.path.join(ROOT, "SOURCES.md")
    if os.path.isfile(sources_md):
        with open(sources_md, encoding="utf-8") as fh:
            registered = ledger_ids(fh.read())

    errors, warnings = validate(manifest, ROOT, registered)
    if registered is None:
        warnings.append("SOURCES.md not found; license-ledger check skipped")

    schema = schema_errors(manifest, os.path.join(ROOT, "SCENES.schema.json"))
    if schema is None:
        warnings.append("jsonschema not installed; full schema check skipped")
    else:
        errors = schema + errors

    for msg in errors:
        print(f"ERROR: {msg}")
    for msg in warnings:
        print(f"WARNING: {msg}")
    print(f"{'FAIL' if errors else 'PASS'}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
