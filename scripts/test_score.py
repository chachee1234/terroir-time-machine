"""Fixtures from GOVERNANCE.md §9. Runs under pytest or `python3 scripts/test_score.py`."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from score import score  # noqa: E402

BACON_DOI = {"title": "Bacon2002", "doi": "10.0000/placeholder"}
ATWATER_CITED = {"title": "Atwater1998"}
ATWATER_DOI = {"title": "Atwater1998", "url": "https://example.org/placeholder"}


class GovernanceFixtures(unittest.TestCase):
    def check(self, result, points, recommendation):
        self.assertEqual(result["feasibility_score"], points)
        self.assertEqual(result["recommendation"], recommendation)

    def test_linked_source_low_effort(self):
        self.check(score([BACON_DOI], 1.5, 0), 80, "auto-approve")

    def test_no_sources_high_effort(self):
        self.check(score([], 10, 0), 0, "needs-data")

    def test_cited_only_mid_effort(self):
        self.check(score([ATWATER_CITED], 4, 3), 41, "needs-data")

    def test_linked_source_mid_effort(self):
        self.check(score([ATWATER_DOI], 4, 3), 61, "backlog")

    def test_backlog_boundary(self):
        self.check(score([ATWATER_DOI], 10, 10), 50, "backlog")

    def test_auto_approve_boundary(self):
        self.check(score([ATWATER_DOI], 4, 10), 75, "auto-approve")


class ThresholdEdges(unittest.TestCase):
    def test_exactly_50_is_backlog(self):
        # 5 (partial) + 15 (4h) + 20 (10 upvotes) + 10 (4h) = 50
        result = score([], 4, 10, data_completeness="partial")
        self.assertEqual(result["feasibility_score"], 50)
        self.assertEqual(result["recommendation"], "backlog")

    def test_exactly_75_is_auto_approve(self):
        # 5 (partial) + 30 (1h) + 20 (10 upvotes) + 20 (1h) = 75
        result = score([], 1, 10, data_completeness="partial")
        self.assertEqual(result["feasibility_score"], 75)
        self.assertEqual(result["recommendation"], "auto-approve")

    def test_upvotes_capped_at_20(self):
        self.assertEqual(score([], 10, 50)["feasibility_score"], 20)

    def test_maximum_is_100(self):
        self.assertEqual(score([BACON_DOI], 1, 10)["feasibility_score"], 100)


if __name__ == "__main__":
    unittest.main()
