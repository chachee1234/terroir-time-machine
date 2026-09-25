"""Tier 0 intake decision for Workflows A/B (GOVERNANCE.md §4, §5).

Turns a Tier 1 Haiku extraction into scorer input, scores it and decides the
state label and comment. No network or model calls; the workflow supplies:

  EXTRACTION  JSON string from the extraction step (may be empty/invalid)
  UPVOTES     count of 👍 reactions on the issue
  LABELS      JSON list of the issue's current label names

Effort is not extracted by the model. It comes from a developer-applied
`effort:<hours>h` label; without one the request is scored as high effort
(0 effort points), so it cannot auto-approve until a human estimates it.

Prints JSON: {"label": ..., "remove": [...], "comment": ..., "score": ...}
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score import score  # noqa: E402

STATE_LABELS = ["approved", "backlog", "needs-data", "extraction-failed"]
EFFORT_LABEL = re.compile(r"^effort:(\d+(?:\.\d+)?)h$")
UNKNOWN_EFFORT_HOURS = 10
REQUIRED_FIELDS = ("location_name", "cited_sources", "data_types", "claimed_ages", "extraction_confidence")


def effort_from_labels(labels):
    for label in labels:
        match = EFFORT_LABEL.match(label)
        if match:
            return float(match.group(1))
    return None


def _number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _in_range(value, low, high):
    value = _number(value)
    return value if value is not None and low <= value <= high else None


def parse_extraction(raw):
    """Return the extraction dict with GOVERNANCE.md §3 field rules applied, or None if unusable.

    Range rules live here rather than in the model's JSON schema, because
    structured outputs do not support numeric constraints.
    """
    try:
        data = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or any(f not in data for f in REQUIRED_FIELDS):
        return None
    if not data.get("location_name") or not isinstance(data.get("cited_sources"), list):
        return None
    confidence = _in_range(data.get("extraction_confidence"), 0, 1)
    if confidence is None:
        return None

    data["extraction_confidence"] = confidence
    data["latitude"] = _in_range(data.get("latitude"), -90, 90)
    data["longitude"] = _in_range(data.get("longitude"), -180, 180)
    gnis = data.get("gnis_id")
    data["gnis_id"] = gnis if isinstance(gnis, int) and not isinstance(gnis, bool) and gnis > 0 else None
    ages = []
    for age in data.get("claimed_ages") or []:
        age_ma = _number(age.get("age_ma")) if isinstance(age, dict) else None
        uncertainty = _number(age.get("uncertainty_ma")) if isinstance(age, dict) else None
        if age_ma is not None and age_ma > 0 and (uncertainty is None or 0 <= uncertainty < age_ma):
            ages.append(age)
    data["claimed_ages"] = ages
    return data


def decide(raw_extraction, upvotes, labels):
    remove = [l for l in STATE_LABELS if l in labels]
    extraction = parse_extraction(raw_extraction)
    if extraction is None:
        return {
            "label": "extraction-failed",
            "remove": [l for l in remove if l != "extraction-failed"],
            "score": None,
            "comment": ("⚠️ Extraction failed. Please edit the issue to include: location name, "
                        "published sources (title and DOI/URL), data types and any published ages."),
        }

    sources = [{"title": s.get("title", ""), "url": s.get("url")}
               for s in extraction["cited_sources"] if isinstance(s, dict) and s.get("title")]
    has_other_data = bool(extraction.get("data_types") or extraction.get("claimed_ages"))
    effort = effort_from_labels(labels)
    result = score(sources, effort if effort is not None else UNKNOWN_EFFORT_HOURS, upvotes,
                   "partial" if has_other_data else None)

    missing = list(result["missing_data"])
    if effort is None:
        missing.append("developer effort estimate (label `effort:<hours>h`)")
    points = result["feasibility_score"]
    rec = result["recommendation"]
    label = {"auto-approve": "approved", "backlog": "backlog", "needs-data": "needs-data"}[rec]

    if rec == "auto-approve":
        comment = f"✅ Score: {points}/100. Approved! Queued for Monday generation."
    elif rec == "backlog":
        comment = f"🟡 Score: {points}/100. Backlog. React 👍 to upvote."
        if missing:
            comment += " Needs: " + "; ".join(missing) + "."
    else:
        comment = f"❌ Score: {points}/100. Missing: " + "; ".join(missing or ["more data"]) + ". Reply with sources."
    comment += f"\n\n<sub>Scoring: {result['reasoning']}</sub>"

    return {"label": label, "remove": [l for l in remove if l != label], "score": points, "comment": comment}


def main():
    labels = json.loads(os.environ.get("LABELS") or "[]")
    upvotes = int(os.environ.get("UPVOTES") or 0)
    print(json.dumps(decide(os.environ.get("EXTRACTION", ""), upvotes, labels)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
