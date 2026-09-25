#!/usr/bin/env bash
# Create or update the permanent issue labels from GOVERNANCE.md §10 (plus effort and digest labels).
# Idempotent. Needs GH_TOKEN with issues: write and REPO=owner/name.
set -euo pipefail

while IFS='|' read -r name color description; do
  gh label create "$name" --repo "$REPO" --color "$color" --description "$description" --force >/dev/null
done <<'EOF'
region-request|1d76db|Incoming region request
approved|0e8a16|Score >= 75, queued for Monday generation
backlog|fbca04|Score 50-74, waiting for upvotes or data
needs-data|d93f0b|Score < 50, blocked on missing data
generated|5319e7|Generated and live
generation-failed|b60205|Pipeline or validation failed
extraction-failed|b60205|Haiku could not parse the issue
type:audit-flag|e11d21|Weekly audit finding for developer review
digest|c5def5|Weekly digest
EOF
