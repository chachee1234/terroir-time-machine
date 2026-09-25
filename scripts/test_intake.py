"""Intake tests. Runs under pytest or `python3 scripts/test_intake.py`. Extractions are made up for testing."""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from intake import decide  # noqa: E402


def extraction(sources=(), data_types=("caldera",), ages=()):
    return json.dumps({
        "location_name": "Crater Lake, Oregon", "latitude": 42.944, "longitude": -122.099, "gnis_id": None,
        "cited_sources": list(sources), "data_types": list(data_types), "claimed_ages": list(ages),
        "extraction_confidence": 0.9,
    })


LINKED = {"title": "Bacon2002", "authors": "Bacon", "year": 2002, "url": "https://doi.org/10.0000/x"}
CITED = {"title": "Atwater1998", "authors": "Atwater", "year": 1998, "url": None}


class IntakeTests(unittest.TestCase):
    def test_invalid_extraction_marks_failed(self):
        for raw in ("", "not json", json.dumps({"location_name": "x"})):
            result = decide(raw, 0, ["region-request", "backlog"])
            self.assertEqual(result["label"], "extraction-failed")
            self.assertEqual(result["remove"], ["backlog"])

    def test_without_effort_label_cannot_auto_approve(self):
        result = decide(extraction([LINKED]), 10, ["region-request"])
        self.assertEqual(result["score"], 50)  # 30 + 0 + 20 + 0
        self.assertEqual(result["label"], "backlog")
        self.assertIn("effort:<hours>h", result["comment"])

    def test_effort_label_enables_approval(self):
        result = decide(extraction([LINKED]), 0, ["region-request", "effort:1.5h"])
        self.assertEqual(result["score"], 80)
        self.assertEqual(result["label"], "approved")
        self.assertIn("✅ Score: 80/100", result["comment"])

    def test_cited_only_needs_data(self):
        result = decide(extraction([CITED]), 3, ["region-request", "effort:4h"])
        self.assertEqual(result["score"], 41)
        self.assertEqual(result["label"], "needs-data")
        self.assertIn("DOI or URL", result["comment"])

    def test_no_sources_but_data_is_partial(self):
        result = decide(extraction([], data_types=["caldera"]), 0, ["effort:1h"])
        self.assertEqual(result["score"], 55)  # 5 + 30 + 0 + 20

    def test_rescore_replaces_old_state_label(self):
        result = decide(extraction([LINKED]), 0, ["region-request", "backlog", "effort:1h"])
        self.assertEqual(result["label"], "approved")
        self.assertEqual(result["remove"], ["backlog"])

    def test_range_rules_applied_in_tier0(self):
        from intake import parse_extraction
        raw = json.loads(extraction([LINKED], ages=[
            {"age_ma": 0.0077, "uncertainty_ma": 0.0001, "citation": "ok"},
            {"age_ma": -5, "uncertainty_ma": None, "citation": "negative"},
            {"age_ma": 2, "uncertainty_ma": 3, "citation": "uncertainty >= age"},
        ]))
        raw.update(latitude=123.0, longitude=-122.1, gnis_id=0)
        data = parse_extraction(json.dumps(raw))
        self.assertIsNone(data["latitude"])
        self.assertEqual(data["longitude"], -122.1)
        self.assertIsNone(data["gnis_id"])
        self.assertEqual([a["citation"] for a in data["claimed_ages"]], ["ok"])

    def test_confidence_out_of_range_is_failed_extraction(self):
        raw = json.loads(extraction([LINKED]))
        raw["extraction_confidence"] = 1.7
        self.assertEqual(decide(json.dumps(raw), 0, [])["label"], "extraction-failed")

    def test_comment_score_is_digest_parseable(self):
        sys.path.insert(0, os.path.dirname(__file__))
        from digest import latest_score
        result = decide(extraction([LINKED]), 0, ["effort:4h"])
        self.assertEqual(latest_score({"comments": [{"body": result["comment"]}]}), result["score"])


if __name__ == "__main__":
    unittest.main()
