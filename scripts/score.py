"""Tier 0 feasibility scorer for region requests.

Implements the scoring rule in GOVERNANCE.md §3 and the output shape in §4.
Pure function, standard library only, no network or model calls.
"""

import json
import sys

AUTO_APPROVE_MIN = 75
BACKLOG_MIN = 50


def _has_link(source):
    return bool(source.get("doi") or source.get("url"))


def score(sources, effort_hours, upvotes=0, data_completeness=None):
    """Score a region request.

    sources: list of dicts with at least "title"; "doi" or "url" marks a linked source.
    effort_hours: estimated effort in hours.
    upvotes: count of upvote reactions/comments.
    data_completeness: "partial" earns 5 points when no sources are cited.
    """
    sources = sources or []
    points = 0
    reasons = []
    missing = []

    # Data availability (0-20 as written in the rule)
    if sources and all(_has_link(s) for s in sources):
        points += 20
        reasons.append("data: all sources linked (+20)")
    elif sources:
        points += 10
        reasons.append("data: sources cited, not all linked (+10)")
        missing.append("DOI or URL for every cited source")
    elif data_completeness == "partial":
        points += 5
        reasons.append("data: partial, no citations (+5)")
        missing.append("published sources")
    else:
        reasons.append("data: none (+0)")
        missing.append("published sources")

    # Technical complexity (0-30)
    if effort_hours <= 2:
        complexity = 30
    elif effort_hours <= 8:
        complexity = 15
    else:
        complexity = 0
    points += complexity
    reasons.append(f"complexity: {effort_hours}h (+{complexity})")

    # Community interest (0-20)
    interest = min(max(upvotes, 0) * 2, 20)
    points += interest
    reasons.append(f"interest: {upvotes} upvotes (+{interest})")

    # Effort estimate (0-20)
    if effort_hours < 2:
        effort = 20
    elif effort_hours < 8:
        effort = 10
    else:
        effort = 0
    points += effort
    reasons.append(f"effort: {effort_hours}h (+{effort})")

    if points >= AUTO_APPROVE_MIN:
        recommendation = "auto-approve"
    elif points >= BACKLOG_MIN:
        recommendation = "backlog"
    else:
        recommendation = "needs-data"

    return {
        "feasibility_score": points,
        "data_available": bool(sources),
        "estimated_effort_hours": effort_hours,
        "recommendation": recommendation,
        "reasoning": "; ".join(reasons),
        "missing_data": missing,
        "sources_found": [s.get("title", "") for s in sources],
    }


def main():
    """Read a request JSON object on stdin, print the score JSON."""
    request = json.load(sys.stdin)
    result = score(
        request.get("sources", []),
        request["effort_hours"],
        request.get("upvotes", 0),
        request.get("data_completeness"),
    )
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
