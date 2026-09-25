"""Digest tests. Runs under pytest or `python3 scripts/test_digest.py`. Issue data is made up for testing."""

import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
from digest import build_digest, latest_score  # noqa: E402

NOW = datetime.datetime(2026, 9, 27, 17, 0, tzinfo=datetime.timezone.utc)


def issue(number, title, state="OPEN", labels=(), closed_at=None, scores=()):
    return {
        "number": number,
        "title": title,
        "state": state,
        "labels": [{"name": name} for name in labels],
        "closedAt": closed_at,
        "comments": [{"body": f"🟡 Score: {s}/100. Backlog."} for s in scores],
    }


class DigestTests(unittest.TestCase):
    def test_latest_score_uses_most_recent_comment(self):
        self.assertEqual(latest_score(issue(1, "a", scores=[55, 63])), 63)
        self.assertIsNone(latest_score(issue(1, "a")))

    def test_counts_only_this_weeks_closures(self):
        issues = [
            issue(1, "Crater Lake", "CLOSED", ["region-request", "generated"], "2026-09-25T09:00:00Z"),
            issue(2, "Old one", "CLOSED", ["generated"], "2026-09-10T09:00:00Z"),
            issue(3, "Dup", "CLOSED", ["needs-data"], "2026-09-26T09:00:00Z"),
        ]
        text = build_digest(issues, NOW)
        self.assertIn("- Issues closed: 2", text)
        self.assertIn("- Regions generated: 1", text)
        self.assertIn("#1 Crater Lake", text)
        self.assertNotIn("Old one", text)

    def test_backlog_top_five_sorted_by_score(self):
        issues = [issue(n, f"R{n}", labels=["backlog"], scores=[50 + n]) for n in range(1, 8)]
        issues.append(issue(20, "Unscored", labels=["backlog"]))
        text = build_digest(issues, NOW)
        listed = [line for line in text.splitlines() if line.startswith("  - #")]
        self.assertEqual([l.split()[1] for l in listed], ["#7", "#6", "#5", "#4", "#3"])

    def test_audit_flags_and_alerts(self):
        issues = [
            issue(9, "Weekly Audit — 2026-09-27", labels=["type:audit-flag"]),
            issue(10, "Shasta", labels=["generation-failed"]),
        ]
        text = build_digest(issues, NOW, tests="23/23", alerts=["⚠️ Weekly quota exceeded. Pausing automation."])
        self.assertIn("- Pending audit flags: 1", text)
        self.assertIn("- Tests passing: 23/23", text)
        self.assertIn("- Generation failed: #10 Shasta", text)
        self.assertIn("Weekly quota exceeded", text)

    def test_unmeasured_metrics_are_not_invented(self):
        text = build_digest([], NOW)
        self.assertIn("- Avg data confidence: not measured", text)
        self.assertIn("- Pages uptime: not measured", text)
        self.assertIn("- Tests passing: not reported", text)
        self.assertIn("## 🚨 Alerts\n- None", text)


if __name__ == "__main__":
    unittest.main()
