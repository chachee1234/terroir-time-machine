"""Deploy tests (GOVERNANCE.md §9). Runs under pytest or `python3 scripts/test_deploy.py [--dry-run]`.

Every test works in a throwaway git repository; nothing touches this repo or any remote.
"""

import datetime
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from deploy import DeployError, execute, plan  # noqa: E402

NOW = datetime.datetime(2026, 9, 28, 9, 0, 0, tzinfo=datetime.timezone.utc)
EMPTY_MANIFEST = {"schema_version": "1.0", "mode": "authoring",
                  "sources": [], "claims": [], "assets": [], "scenes": []}


def git(root, *args):
    return subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *args],
                          cwd=root, capture_output=True, text=True, check=True).stdout


class DeployTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = self._tmp.name
        git(self.root, "init", "-q", "-b", "main")
        with open(os.path.join(self.root, "README.md"), "w") as fh:
            fh.write("test\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "init")
        self.write_region("crater", EMPTY_MANIFEST)

    def tearDown(self):
        self._tmp.cleanup()

    def write_region(self, region_id, manifest):
        region = os.path.join(self.root, "regions", region_id)
        os.makedirs(region, exist_ok=True)
        with open(os.path.join(region, "SCENES.json"), "w") as fh:
            json.dump(manifest, fh)

    def test_dry_run_plans_without_side_effects(self):
        steps = plan("crater", 82, self.root, NOW)
        self.assertEqual(steps[0], ("copy", "regions/crater", "docs/regions/crater"))
        self.assertIn(("git", "commit", "-m", "Auto-generated: crater, Score: 82"), steps)
        self.assertIn(("git", "push", "origin", "auto-20260928-090000-crater"), steps)
        self.assertFalse(os.path.exists(os.path.join(self.root, "docs")))
        self.assertEqual(git(self.root, "rev-list", "--count", "HEAD").strip(), "1")

    def test_rejects_bad_region_id(self):
        with self.assertRaisesRegex(DeployError, "invalid region id"):
            plan("../etc", 80, self.root, NOW)

    def test_rejects_missing_region(self):
        with self.assertRaisesRegex(DeployError, "missing regions/nowhere"):
            plan("nowhere", 80, self.root, NOW)

    def test_rejects_bad_score(self):
        with self.assertRaisesRegex(DeployError, "score must be"):
            plan("crater", 101, self.root, NOW)

    def test_rejects_failed_validation(self):
        bad = dict(EMPTY_MANIFEST, scenes=[{"id": "s", "time": {"older_ma": 40, "younger_ma": 50}}])
        self.write_region("crater", bad)
        with self.assertRaisesRegex(DeployError, "validation failed"):
            plan("crater", 80, self.root, NOW)

    def test_rejects_changes_outside_commit_scope(self):
        with open(os.path.join(self.root, "README.md"), "a") as fh:
            fh.write("edit\n")
        with self.assertRaisesRegex(DeployError, "changes outside regions/ and docs/: README.md"):
            plan("crater", 80, self.root, NOW)

    def test_local_deploy_commits_only_region_paths_and_tags(self):
        env = {"GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
               "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid"}
        old_env = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            execute(plan("crater", 82, self.root, NOW), self.root, push=False)
        finally:
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        files = git(self.root, "show", "--name-only", "--format=", "HEAD").split()
        self.assertEqual(sorted(files), ["docs/regions/crater/SCENES.json", "regions/crater/SCENES.json"])
        self.assertIn("auto-20260928-090000-crater", git(self.root, "tag"))


if __name__ == "__main__":
    unittest.main(argv=[a for a in sys.argv if a != "--dry-run"])
