"""Tier 0 deploy step for Workflow C (GOVERNANCE.md §5, §7).

Publishes one generated region: validates regions/<region_id>/SCENES.json, copies
the region to docs/regions/<region_id>, commits only those two paths, tags the
commit for rollback and pushes. Refuses to run if the working tree has changes
outside regions/ and docs/ (GOVERNANCE.md §3 commit scope).

Usage:
  python3 scripts/deploy.py <region_id> <score> [--dry-run] [--no-push]

--dry-run runs the read-only checks and prints the plan; it copies, commits,
tags and pushes nothing.
"""

import datetime
import json
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import ROOT, schema_errors, validate  # noqa: E402

REGION_ID = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*$")
ALLOWED_PREFIXES = ("regions/", "docs/")


class DeployError(Exception):
    pass


def _git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if result.returncode != 0:
        raise DeployError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _changed_paths(root):
    paths = []
    for line in _git(root, "status", "--porcelain", "--untracked-files=all").splitlines():
        path = line[3:]
        if " -> " in path:
            paths.extend(path.split(" -> "))
        else:
            paths.append(path)
    return [p.strip('"') for p in paths]


def plan(region_id, score, root=ROOT, now=None):
    """Run read-only checks and return the list of planned steps."""
    if not REGION_ID.match(region_id or ""):
        raise DeployError(f"invalid region id '{region_id}'")
    if not isinstance(score, int) or not 0 <= score <= 100:
        raise DeployError(f"score must be an integer 0-100, got {score!r}")

    region_dir = os.path.join(root, "regions", region_id)
    manifest_path = os.path.join(region_dir, "SCENES.json")
    if not os.path.isfile(manifest_path):
        raise DeployError(f"missing regions/{region_id}/SCENES.json")
    try:
        with open(manifest_path) as fh:
            manifest = json.load(fh)
    except json.JSONDecodeError as exc:
        raise DeployError(f"regions/{region_id}/SCENES.json is not valid JSON: {exc}")
    errors, _ = validate(manifest, root)
    errors = (schema_errors(manifest, os.path.join(ROOT, "SCENES.schema.json")) or []) + errors
    if errors:
        raise DeployError("validation failed: " + "; ".join(errors))

    outside = [p for p in _changed_paths(root) if not p.startswith(ALLOWED_PREFIXES)]
    if outside:
        raise DeployError("changes outside regions/ and docs/: " + ", ".join(sorted(outside)))

    stamp = (now or datetime.datetime.now(datetime.timezone.utc)).strftime("%Y%m%d-%H%M%S")
    message = f"Auto-generated: {region_id}, Score: {score}"
    tag = f"auto-{stamp}-{region_id}"
    return [
        ("copy", f"regions/{region_id}", f"docs/regions/{region_id}"),
        ("git", "add", f"regions/{region_id}", f"docs/regions/{region_id}"),
        ("git", "commit", "-m", message),
        ("git", "tag", "-a", tag, "-m", message),
        ("git", "push", "origin", "main"),
        ("git", "push", "origin", tag),
    ]


def execute(steps, root=ROOT, push=True):
    for step in steps:
        if step[0] == "copy":
            src, dst = os.path.join(root, step[1]), os.path.join(root, step[2])
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        elif step[1] == "push" and not push:
            continue
        else:
            _git(root, *step[1:])


def main(argv):
    flags = {a for a in argv[1:] if a.startswith("--")}
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 2 or not args[1].isdigit():
        print(__doc__.strip())
        return 2
    region_id, score = args[0], int(args[1])
    try:
        steps = plan(region_id, score)
        for step in steps:
            print(("DRY-RUN: " if "--dry-run" in flags else "") + " ".join(step))
        if "--dry-run" not in flags:
            execute(steps, push="--no-push" not in flags)
            print(f"Deployed {region_id}")
    except DeployError as exc:
        print(f"ERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
