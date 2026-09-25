"""Tier 0 weekly digest (GOVERNANCE.md §5 Workflow E, §10).

Builds the Sunday digest markdown from issue data. No network access: the
workflow fetches issues and pipes them in, e.g.

  gh issue list --state all --limit 500 \
    --json number,title,state,labels,closedAt,comments \
    | python3 scripts/digest.py --tests 23/23

Metrics the repository cannot measure deterministically (average extraction
confidence, Pages uptime) are reported as "not measured" rather than estimated.
"""

import argparse
import datetime
import json
import re
import sys

SCORE = re.compile(r"Score(?: updated)?:\s*(\d{1,3})/100")


def _labels(issue):
    return {label["name"] if isinstance(label, dict) else label for label in issue.get("labels", [])}


def _parse_time(value):
    if not value:
        return None
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def latest_score(issue):
    """Most recent 'Score: N/100' posted on the issue, or None."""
    score = None
    for comment in issue.get("comments", []):
        match = None
        for match in SCORE.finditer(comment.get("body", "")):
            pass
        if match:
            score = int(match.group(1))
    return score


def build_digest(issues, now, tests=None, alerts=()):
    week_start = now - datetime.timedelta(days=7)

    def closed_this_week(issue):
        closed = _parse_time(issue.get("closedAt"))
        return issue.get("state", "").upper() == "CLOSED" and closed and closed >= week_start

    closed = [i for i in issues if closed_this_week(i)]
    generated = [i for i in closed if "generated" in _labels(i)]
    failed = [i for i in issues if i.get("state", "").upper() == "OPEN" and "generation-failed" in _labels(i)]
    audit_flags = [i for i in issues if i.get("state", "").upper() == "OPEN" and "type:audit-flag" in _labels(i)]
    backlog = [i for i in issues if i.get("state", "").upper() == "OPEN" and "backlog" in _labels(i)]
    backlog.sort(key=lambda i: (latest_score(i) is None, -(latest_score(i) or 0), i["number"]))

    lines = [f"# TTM weekly digest — week ending {now:%Y-%m-%d}", "", "## ✅ Completed this week"]
    lines.append(f"- Issues closed: {len(closed)}")
    lines.append(f"- Regions generated: {len(generated)}")
    lines.extend(f"  - #{i['number']} {i['title']}" for i in generated)

    lines += ["", "## ⏳ In progress"]
    if backlog:
        lines.append("- Top backlog regions:")
        for i in backlog[:5]:
            score = latest_score(i)
            lines.append(f"  - #{i['number']} {i['title']} — score {score if score is not None else 'unknown'}/100")
    else:
        lines.append("- Backlog regions: none")
    lines.append(f"- Pending audit flags: {len(audit_flags)}")
    lines.extend(f"  - #{i['number']} {i['title']}" for i in audit_flags)

    lines += ["", "## 📊 Metrics"]
    lines.append(f"- Tests passing: {tests if tests else 'not reported'}")
    lines.append("- Avg data confidence: not measured")
    lines.append("- Pages uptime: not measured")

    all_alerts = list(alerts) + [f"Generation failed: #{i['number']} {i['title']}" for i in failed]
    lines += ["", "## 🚨 Alerts"]
    if all_alerts:
        lines.extend(f"- {a}" for a in all_alerts)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def main(argv):
    parser = argparse.ArgumentParser(description="Build the weekly digest from gh issue JSON on stdin.")
    parser.add_argument("--tests", help="test result as passed/total, e.g. 23/23")
    parser.add_argument("--alert", action="append", default=[], help="extra alert line (repeatable)")
    args = parser.parse_args(argv[1:])
    issues = json.load(sys.stdin)
    now = datetime.datetime.now(datetime.timezone.utc)
    sys.stdout.write(build_digest(issues, now, args.tests, args.alert))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
