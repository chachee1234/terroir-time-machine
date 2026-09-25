"""Fixtures from GOVERNANCE.md §9. Runs under pytest or `python3 scripts/test_validate.py`.

Fixtures are in-memory test data only, not production scenes or source records.
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from validate import ROOT, ledger_ids, validate  # noqa: E402


def scene(scene_id, older, younger, keyframe_ages=(), asset_ids=()):
    return {
        "id": scene_id,
        "time": {"older_ma": older, "younger_ma": younger, "precision_note": "test"},
        "asset_ids": list(asset_ids),
        "keyframes": [{"age_ma": a, "asset_ids": list(asset_ids)} for a in keyframe_ages],
        "claim_ids": [],
    }


def manifest(scenes=(), sources=(), claims=(), assets=()):
    return {"schema_version": "1.0", "mode": "authoring", "sources": list(sources),
            "claims": list(claims), "assets": list(assets), "scenes": list(scenes)}


class GovernanceFixtures(unittest.TestCase):
    def test_repository_manifest_passes(self):
        with open(os.path.join(ROOT, "SCENES.json")) as fh:
            errors, _ = validate(json.load(fh))
        self.assertEqual(errors, [])

    def test_missing_ledger_entry_warns(self):
        errors, warnings = validate(manifest(sources=[{"id": "X99"}]), registered_ids={"G01"})
        self.assertEqual(errors, [])
        self.assertEqual(warnings, ["source 'X99': no entry in SOURCES.md"])

    def test_keyframe_inside_interval_passes(self):
        errors, _ = validate(manifest([scene("s1", 1000, 500, [750])]))
        self.assertEqual(errors, [])

    def test_keyframe_outside_interval_fails(self):
        errors, _ = validate(manifest([scene("s1", 50, 40, [100])]))
        self.assertEqual(len(errors), 1)
        self.assertIn("outside scene interval", errors[0])


class AgeRules(unittest.TestCase):
    def test_inverted_interval_fails(self):
        errors, _ = validate(manifest([scene("s1", 40, 50)]))
        self.assertIn("older_ma 40 < younger_ma 50", errors[0])

    def test_scenes_must_run_oldest_to_youngest(self):
        errors, _ = validate(manifest([scene("young", 10, 0), scene("old", 1000, 500)]))
        self.assertIn("not ordered oldest to youngest", errors[0])

    def test_keyframes_must_run_oldest_to_youngest(self):
        errors, _ = validate(manifest([scene("s1", 1000, 500, [600, 900])]))
        self.assertIn("keyframes not ordered", errors[0])


class References(unittest.TestCase):
    def test_duplicate_ids_fail(self):
        errors, _ = validate(manifest([scene("s1", 10, 0), scene("s1", 5, 0)]))
        self.assertIn("duplicate id 's1'", errors[0])

    def test_unknown_claim_and_source_fail(self):
        s = scene("s1", 10, 0)
        s["claim_ids"] = ["c_missing"]
        claim = {"id": "c1", "evidence": [{"source_id": "G_missing"}]}
        errors, _ = validate(manifest([s], claims=[claim]))
        self.assertIn("scene 's1': unknown claim 'c_missing'", errors)
        self.assertIn("claim 'c1': unknown source 'G_missing'", errors)

    def test_asset_file_and_checksum(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "assets"))
            data = b"test asset"
            with open(os.path.join(root, "assets", "a.bin"), "wb") as fh:
                fh.write(data)
            good = {"id": "a1", "path": "assets/a.bin", "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest()}
            self.assertEqual(validate(manifest(assets=[good]), root)[0], [])

            bad = dict(good, sha256="0" * 64)
            self.assertEqual(validate(manifest(assets=[bad]), root)[0], ["asset 'a1': sha256 mismatch"])

            missing = dict(good, path="assets/none.bin")
            self.assertIn("file not found", validate(manifest(assets=[missing]), root)[0][0])


class Ledger(unittest.TestCase):
    def test_reads_repository_sources_md(self):
        with open(os.path.join(ROOT, "SOURCES.md"), encoding="utf-8") as fh:
            ids = ledger_ids(fh.read())
        self.assertTrue({"G01", "G07", "G13", "T03"} <= ids)
        self.assertNotIn("ID", ids)


if __name__ == "__main__":
    unittest.main()
