# GOVERNANCE.md

**Terroir Time Machine — Autonomous Operations Policy**

Version: 1.2  
Effective: September 20, 2026  
Last revised: September 24, 2026 (v1.2: OAuth token lifetime is 1 year, rotate yearly; v1.1: all-linked sources award raised from 20 to 30 so the maximum score is 100)  
Authority: Developer + Claude Agent (within defined rules)

---

## 1. OVERVIEW

TTM is an autonomous open-source application for geological history exploration. This document defines:
- Which decisions are automated, which require human approval
- Model allocation: Haiku 4.5 (extraction) + Opus 5.5 (audits only)
- Tier 0 (deterministic Python) runs most operations
- Quota management against Claude Pro shared weekly limit
- Escalation ladder for edge cases

**Core principle:** Automation is permitted only when the decision rule is auditable, repeatable, and testable. If humans can't verify the logic, humans must make the call.

---

## 2. MODEL POLICY

**Locked models:**
- `claude-haiku-4-5-20251001` — Text extraction, classification (Tier 1)
- `claude-opus-5-5` — Weekly architecture audit (Tier 2)
- No other models. No Fable. No Sonnet. No direct API calls via SDK.

**Authentication:**
- All runs use `CLAUDE_CODE_OAUTH_TOKEN` (generated via `claude setup-token`)
- OAuth token binds all model usage to Claude Pro subscription
- Marginal cost: $0 (consumption against shared weekly quota only)
- Separate from API billing; no "overage fees"

**Token rotation:**
- Tokens from `claude setup-token` are valid for 1 year (stated by the CLI at creation)
- Calendar reminder: `Rotate CLAUDE_CODE_OAUTH_TOKEN` 11 months after creation (one month before expiry)
- Rotate immediately if a token is ever exposed (pasted in chat, logs, screenshots)
- Test token validity in Phase 2 before adding Haiku to critical path

---

## 3. TIER DEFINITIONS

### **Tier 0 — Deterministic Python (No Models)**

Runs any time, zero quota impact. Pure functions. Testable offline.

| Operation | Trigger | Input | Output | Owner |
|---|---|---|---|---|
| **Score calculation** | Haiku extraction complete | Structured JSON (location, sources, effort, upvotes, age ranges) | Score (0–100), recommendation, reasoning | `scripts/score.py` |
| **Schema validation** | Every commit to `regions/` or `data/` | Evidence Package JSON | Pass/Fail + error list | `scripts/validate.py` |
| **Age-range sanity** | During validation | Chapter ages, ranges, confidence | Warnings if ranges contradictory | `scripts/validate.py` |
| **License-ledger check** | During validation | SOURCES.md, source IDs in JSON | Warnings if entries missing or mismatched | `scripts/validate.py` |
| **Cross-reference integrity** | During validation | Region references, file paths | Errors if files referenced don't exist | `scripts/validate.py` |
| **Generation execution** | Monday 9 AM UTC | `data/{region_id}.json` exists, approved | Runs `src/pipeline/generate_region.py` | `.github/workflows/phase1-monday.yml` |
| **Git operations** | After validation passes | Staged files, commit message | Commits, pushes, syncs to GitHub Pages | `scripts/deploy.py` |
| **Digest assembly** | Sunday 4 PM UTC | Repo metadata, issue labels, closed PRs | Email-ready markdown | `scripts/digest.py` |
| **Issue auto-close** | Weekly (Monday) | Issues labeled `needs-data` + no comment in 7 days | Closes with template comment | Workflow |
| **Label management** | Event-driven | Issue number, action | Adds/removes labels based on state | Workflow |

**Scoring rule (pseudocode):**
```
function score(location, sources, effort_hours, upvotes, data_completeness):
  points = 0
  
  # Data availability (0–30 pts)
  if sources.length > 0 and sources all have DOI/URL:
    points += 30
  elif sources.length > 0 and some have citations:
    points += 10
  elif data_completeness == "partial":
    points += 5
  
  # Technical complexity (0–30 pts)
  if effort_hours <= 2:
    points += 30
  elif effort_hours <= 8:
    points += 15
  else:
    points += 0
  
  # Community interest (0–20 pts)
  points += min(upvotes * 2, 20)
  
  # Effort estimate penalty (0–20 pts)
  if effort_hours < 2:
    points += 20
  elif effort_hours < 8:
    points += 10
  else:
    points += 0
  
  # Recommendation logic
  if points >= 75:
    return { score: points, recommendation: "auto-approve", next_action: "Queue Monday generation" }
  elif points >= 50:
    return { score: points, recommendation: "backlog", next_action: "Wait for upvotes or data" }
  else:
    return { score: points, recommendation: "needs-data", next_action: "Comment with missing pieces" }
```

**Commit scope:** The only Tier 0 operation that commits to `main` is the Workflow C deploy step, and it may only commit generated region output (`regions/`, `docs/`) after validation passes. Every other change — code, workflows, scoring rules, data files, this document — is staged, validated, and reported to the developer, and merges only after developer approval.

---

### **Tier 1 — Haiku Extraction (Text Classification)**

Runs on GitHub issue events (created, commented). Deterministic JSON output feeds Tier 0 scorer.

**Single job:** Extract structured fields from free-text region requests.

| Field | Type | Example | Validation |
|---|---|---|---|
| `location_name` | string | "Crater Lake, Oregon" | Non-empty |
| `latitude` | float | 42.944 | -90 to 90 |
| `longitude` | float | -122.099 | -180 to 180 |
| `gnis_id` | int or null | 227505 | Positive or null |
| `cited_sources` | array of {title, authors, year, url} | [{title: "Bacon et al. 2002", url: "..."}] | At least title |
| `data_types` | array | ["volcano", "caldera", "ash-flow tuff"] | Non-empty |
| `claimed_ages` | array of {age_ma, uncertainty_ma, citation} | [{age_ma: 7500, uncertainty_ma: 500}] | age_ma > 0, uncertainty < age |
| `extraction_confidence` | float 0–1 | 0.92 | Must be present |

**Prompt (read-only, no decision-making):**

```
Extract geological data from the issue body below.
Return ONLY valid JSON. Do not comment, score, or decide.

Issue body:
{issue_body}

Return this structure:
{
  "location_name": "string",
  "latitude": <number or null>,
  "longitude": <number or null>,
  "gnis_id": <int or null>,
  "cited_sources": [
    {"title": "...", "authors": "...", "year": <int>, "url": "..."}
  ],
  "data_types": ["..."],
  "claimed_ages": [
    {"age_ma": <number>, "uncertainty_ma": <number>, "citation": "..."}
  ],
  "extraction_confidence": <0–1>
}

If any field cannot be extracted, set to null or empty array.
```

**Fallback:** If Haiku fails or returns invalid JSON, the workflow posts a comment asking for clarification, labels the issue `extraction-failed`, and stops. No escalation to Tier 2.

**Comment classification (bonus):**

Also classify new comments as:
- `upvote` — expresses support or interest
- `new-data` — provides published references or ages
- `noise` — clarification question, not new information

Tier 0 uses this to decide: re-score on `new-data`, increment upvotes on `upvote`, ignore `noise`.

**Quota:** Negligible. Haiku extractions are ~200 input tokens, ~100 output tokens each. ~15 per week = ~4,500 tokens/week.

---

### **Tier 2 — Opus Weekly Audit**

Scheduled: **Sunday 16:00 UTC** (the day before Monday's Phase 1 generation run).  
Never auto-commits. Always opens an issue for human review.

**Single job:** Review the past week's diff. Flag issues, not solutions.

**Scope (in order, stops at first blocker):**

1. **Security:** Any new external HTTP calls, new dependencies, changes to workflow YAML
2. **License drift:** New source files added without corresponding SOURCES.md entries
3. **Scoring misfires:** Cases where Tier 0 rule gave a score the math doesn't justify (e.g., missing upvotes counted twice)
4. **Code quality:** Dead code, unused imports, obvious inefficiencies in changed files only
5. **Architecture drift:** Any new pipeline step touching GPL/permissive boundary

**Prompt (diff-scoped, bounded):**

```
You are the weekly architecture auditor for Terroir Time Machine.
Review ONLY the changes from the past 7 days (below).
Do NOT review the entire repo.

Changes since last Sunday:
{git_diff --since="7 days ago"}

Audit checklist (stop at first issue; do not list "all" issues):
1. Security: Any new external calls, dependencies, YAML changes?
2. License: New sources without SOURCES.md?
3. Scoring: Any obvious math errors in the scoring rule?
4. Code: Any unused imports or dead code in changed files?
5. Architecture: Any GPL/permissive boundary violations?

Output ONE issue per blocker found, or "✅ Clear" if none.
Format:
**Type:** [Security|License|Scoring|Code|Architecture]
**Finding:** [one sentence]
**File(s):** [which files]
**Recommendation:** [what to check or fix]
```

**Output:** One GitHub issue titled `Weekly Audit — YYYY-MM-DD`.

**Max turns:** 3 (if Opus gets confused and loops, the workflow halts after 3 turns and opens a separate `Audit Failed` issue).

**Cost:** One bounded Opus run per week. ~2000 input tokens (diff size varies), ~500 output. ~3,500 tokens/week. Well under shared quota.

**Escalation:** Any issue opened by Tier 2 is marked `type:audit-flag` and waits for human review. The audit never merges, never closes its own issues, never removes labels.

---

## 4. SCORING ALGORITHM

**Input:** Structured JSON from Haiku (or manual input for testing)

**Processing:** Tier 0 Python function (see pseudocode above)

**Output:**
```json
{
  "feasibility_score": 0–100,
  "data_available": true|false,
  "estimated_effort_hours": integer,
  "recommendation": "auto-approve|backlog|needs-data",
  "reasoning": "string",
  "missing_data": ["item1", "item2"],
  "sources_found": ["source1", "source2"]
}
```

**Decision rule:**
- **Score ≥ 75:** Auto-approve → label `approved`, queue for Monday generation
- **Score 50–74:** Backlog → label `backlog`, comment "Score: X/100. Needs upvotes or data to approve. React 👍 to upvote."
- **Score < 50:** Needs data → label `needs-data`, comment "Missing: [list]. Comment with sources."

**Boundary scores:** Thresholds are inclusive — exactly 50 → backlog, exactly 75 → auto-approve. Scores are integers, so no rounding is needed.

---

## 5. OPERATION WORKFLOWS

### **Workflow A: New Region Request (Issue Opens)**

```
User opens issue with label: region-request
  ↓
GitHub Actions: on-issue.yml triggered
  ↓
Claude Haiku: Extract fields from issue body
  ↓
Validation: JSON schema check
  ↓ (if invalid)
Post comment: "Extraction failed. Please provide: [fields]"
Stop.
  ↓ (if valid)
Tier 0: score(fields)
  ↓ (score ≥ 75)
Post comment: "✅ Score: 82/100. Approved! Queued for Monday generation."
Add label: "approved"
  ↓ (50–74)
Post comment: "🟡 Score: 63/100. Backlog. Needs [specific thing]. React 👍 to upvote!"
Add label: "backlog"
  ↓ (<50)
Post comment: "❌ Score: 42/100. Missing: [list]. Reply with sources."
Add label: "needs-data"
Stop.
```

### **Workflow B: Comment on Region Request**

```
User comments on region-request issue
  ↓
GitHub Actions: on-issue.yml triggered (same as A)
  ↓
Claude Haiku: Classify comment (upvote|new-data|noise)
  ↓ (if upvote)
Tier 0: Increment upvote counter, re-score
  ↓
Update comment on issue: "Score updated: 65/100 (↑ 1 upvote)"
  ↓ (if new-data)
Haiku: Extract sources, re-score
Tier 0: Re-score with new sources
  ↓
Update comment: "Score updated: 78/100 (new source accepted)"
If score now ≥ 75, add "approved" label
  ↓ (if noise)
Stop (no action).
```

### **Workflow C: Monday Morning Generation**

```
Monday 9 AM UTC: Scheduled cron fires
  ↓
Tier 0: Scan all issues labeled "approved"
  ↓ (none found)
Log: "No approved regions."
Stop.
  ↓ (found N issues)
For each approved issue:
  ↓
  Tier 0: Load region data file (data/{region_id}.json)
  ↓ (file not found)
  Post comment on issue: "❌ Data file not found."
  Add label: "generation-failed"
  Stop (next issue).
  ↓ (file found)
  Run: python src/pipeline/generate_region.py
  ↓ (pipeline fails)
  Post comment: "❌ Generation failed: [error]"
  Add label: "generation-failed"
  Stop (next issue).
  ↓ (pipeline succeeds)
  Tier 0: Validate output (schema, ages, licenses)
  ↓ (validation fails)
  Post comment: "❌ Validation failed: [error]"
  Add label: "generation-failed"
  Stop (next issue).
  ↓ (validation passes)
  Tier 0: Deploy (generated output only — see §3 Commit scope)
    - Copy to docs/
    - git add regions/, docs/
    - git commit -m "Auto-generated: [region], Score: [score]"
    - git push origin main
    - (GitHub Pages auto-syncs)
  ↓
  Post comment: "✅ Generated & deployed! Live at: https://[URL]"
  Remove label: "approved"
  Add label: "generated"
  Close issue
  ↓ (all issues processed)
  Log completion.
```

### **Workflow D: Sunday Audit**

```
Sunday 16:00 UTC: Scheduled cron fires
  ↓
Tier 0: Fetch git diff from past 7 days
  ↓
Claude Opus: Audit diff (max 3 turns)
  ↓ (Opus returns clear)
  Log: "✅ Weekly audit: No issues."
  Stop.
  ↓ (Opus flags issue)
  Tier 0: Create issue titled "Weekly Audit — [date]"
    - Body: Opus findings
    - Label: "type:audit-flag"
    - Assign: developer
  Stop (issue waits for review).
```

### **Workflow E: Weekly Digest**

```
Sunday 17:00 UTC (after audit completes): Scheduled cron fires
  ↓
Tier 0: Assemble digest from repo state
  - Count closed issues this week
  - Count generated regions
  - List open backlog (top 5 by score)
  - Report metrics: avg confidence, test pass rate, Pages uptime
  - List any audit flags from Workflow D
  ↓
Tier 0: Build markdown email
  ↓
Tier 0: Send via GitHub (create discussion) or email API
  ↓
Done.
```

---

## 6. QUOTA MANAGEMENT

**Shared pool:** Claude Pro subscription has one weekly limit across all surfaces (Claude.ai, Claude Code, desktop/mobile). All model usage competes for the same budget.

**Constraints:**
- Rolling 5-hour session window
- Fixed weekly cap (reset day/time assigned to account)

**Monthly baseline (conservative, testing):**

| Operation | Frequency | Model | Tokens | Weekly | Monthly |
|---|---|---|---|---|---|
| Haiku extraction | 10–15 issues | Haiku | 300 each | 4.5K | 18K |
| Opus audit | 1 run | Opus | 2.5K | 2.5K | 10K |
| **Total** | | | | **7K** | **28K** |

**Your development:** Assume your own Claude.ai usage consumes 50–70% of weekly quota.

**Headroom:** Autonomous operations target <10% of weekly budget, leaving 20–30% as safety margin.

**If you exceed headroom:**
- Workflows log a warning
- If weekly cap reached mid-week, next scheduled run is skipped
- You receive notification in digest: "⚠️ Weekly quota exceeded. Pausing automation."

---

## 7. SAFEGUARDS & KILL SWITCHES

### **Enable/Disable**

Repo variable `AGENT_ENABLED` (true/false).

Checked first in every GitHub Actions workflow:
```yaml
- name: Check if automation is enabled
  if: vars.AGENT_ENABLED != 'true'
  run: echo "Automation disabled. Exiting." && exit 0
```

To pause all automation without editing code: Settings → Repo variables → toggle `AGENT_ENABLED=false`.

### **Max Turns (Tier 2 only)**

Opus audit workflow capped at 3 turns. After 3 turns:
```python
if turns >= 3:
  print("Max turns reached. Opening escalation issue.")
  create_issue("Weekly Audit Failed — Max Turns", "Opus audit looped 3x. Manual review required.")
  exit(1)
```

### **Never Auto-Merge**

- Tier 0: Stages files, runs validation, waits for developer. Sole exception: Workflow C pushes validated generated output (`regions/`, `docs/`) — see §3 Commit scope
- Tier 1: Posts comments, adds labels, waits
- Tier 2: Opens issues, waits
- Pull requests and all non-generated changes merge to main only by the developer

### **Token Expiry**

OAuth token from `claude setup-token` expires 1 year after creation.

If token invalid:
```
GitHub Actions: claude-code-action returns "auth failed"
→ Workflow fails with message: "CLAUDE_CODE_OAUTH_TOKEN expired or invalid"
→ Developer receives alert
→ Developer runs: claude setup-token, updates secret
```

**Reminder:** Calendar task "Rotate CLAUDE_CODE_OAUTH_TOKEN" 11 months after each rotation.

### **Rollback Always Available**

Every commit is tagged with:
```
git tag -a auto-YYYYMMDD-HHMMSS-<region_id> -m "Auto-generated: <reason>"
git push --tags
```

To revert:
```
git revert <commit_hash>
git push
```

Or delete from Pages:
```
rm -rf docs/regions/<region_id>
git add docs/
git commit -m "Revert region: <reason>"
git push
```

---

## 8. ESCALATION LADDER

**Tier 0 → Human:** Anything deterministic Python can't decide.

| Scenario | Decision | Escalation |
|---|---|---|
| Haiku extraction fails | Mark issue `extraction-failed`, stop | Developer: Review issue manually |
| Score < 50 (needs data) | Label `needs-data`, comment with missing pieces | Developer: Provide data or close issue |
| Validation fails | Label `generation-failed`, log error | Developer: Fix data file or data source |
| Opus audit flags security issue | Open `type:audit-flag` issue | Developer: Review and decide fix |
| New external dependency proposed | Audit flags it, stops | Developer: Approve or reject in review |
| License ambiguity | Audit flags it | Developer: Consult external source, update SOURCES.md |
| Quota exceeded mid-week | Next generation skipped, logged | Developer: Manually trigger high-priority generation or skip |
| Token expired | Workflow fails with error | Developer: `claude setup-token`, update secret |

**Humans decide:**
- License interpretation (GPL v2 compatibility, open-source definitions)
- External data source trust (new Macrostrat API version, USGS datasource changes)
- Architecture changes (new pipeline step, new event type)
- Dependency updates (new Python package for validation)

**Automated always:**
- Scoring (rule-based, auditable)
- Generation (if data passes validation)
- Deployment of generated region output only (if generation passes validation)
- Validation (schema, age ranges, cross-references)

---

## 9. TESTING & VALIDATION

### **Phase 1 Testing (Tier 0 only)**

```bash
# Test score.py
python -m pytest scripts/test_score.py

# Fixtures (expected values follow the §3 scoring rule exactly):
# - score(sources=["Bacon2002" w/ DOI], effort=1.5, upvotes=0) → 80 (30+30+0+20) → auto-approve
# - score(sources=[], effort=10, upvotes=0, completeness="none") → 0 (0+0+0+0) → needs-data
# - score(sources=["Atwater1998" citation only, no DOI], effort=4, upvotes=3) → 41 (10+15+6+10) → needs-data
# - score(sources=["Atwater1998" w/ DOI], effort=4, upvotes=3) → 61 (30+15+6+10) → backlog
# - score(sources=["Atwater1998" w/ DOI], effort=10, upvotes=10) → 50 (30+0+20+0) → backlog (boundary)
# - score(sources=["Atwater1998" w/ DOI], effort=4, upvotes=10) → 75 (30+15+20+10) → auto-approve (boundary)

# Test validate.py
python -m pytest scripts/test_validate.py

# Fixtures:
# - Valid TIMELINE.json → pass
# - Missing SOURCES.md entry → warning
# - Age range 1000–500 for chapter at 750 Ma → pass
# - Age range 50–40 for chapter at 100 Ma → fail

# Test deploy.py
# (dry-run only, no actual git)
python scripts/test_deploy.py --dry-run
```

### **Phase 2 Testing (Haiku extraction)**

Manually create test issues with these bodies:
1. Clean, well-sourced request → expect `extraction_confidence > 0.9`
2. Vague request ("famous volcano in South America") → expect `extraction_confidence < 0.7`
3. Invalid lat/lon → expect `latitude=null`
4. No citations → expect `cited_sources=[]`

Confirm Haiku output is valid JSON every time.

### **Phase 3 Testing (Opus audit)**

Run the audit manually on a test repo commit. Confirm:
- It runs in <5 minutes
- Quota consumed <5000 tokens
- Output is a valid GitHub issue

---

## 10. MONITORING & REPORTING

### **Digest (Every Sunday)**

Developer receives email/discussion with:
```
✅ COMPLETED THIS WEEK
  • Regions generated: [N]
  • Validation passes: [N]
  • Deployments successful: [N]

⏳ IN PROGRESS
  • Backlog regions: [list with scores]
  • Pending audit flags: [N]

📊 METRICS
  • Avg data confidence: X%
  • Tests passing: Y/Y
  • Pages uptime: Z%

🚨 ALERTS
  • [If any]
```

### **Issue Labels (Permanent)**

- `region-request` — incoming region requests
- `approved` — score ≥75, queued for generation
- `backlog` — score 50–74, waiting for interest
- `needs-data` — score <50, blocked on missing data
- `generated` — successfully generated and live
- `generation-failed` — pipeline or validation failed
- `extraction-failed` — Haiku couldn't parse the issue
- `type:audit-flag` — Opus flagged an issue for review

---

## 11. DECISION AUTHORITY

| Decision | Authority | Can Delegate |
|---|---|---|
| Enable/disable automation | Developer | No (repo admin only) |
| Approve flagged audit issues | Developer | Yes (code review) |
| Merge pull requests | Developer | Yes (code review) |
| Accept region requests (manual) | Developer | No |
| Rotate OAuth token | Developer | No |
| Change GOVERNANCE.md | Developer | No (must amend this file) |
| Modify scoring rule | Developer | No (amendment + tests required) |
| Update dependencies | Developer | Yes (code review) |

---

## 12. AMENDMENT PROCESS

To change this policy:

1. Edit this file
2. Update version & effective date
3. Document reasoning in a comment
4. Commit with message: `Update GOVERNANCE.md: [brief change]`
5. Tag: `git tag governance-vX.X`
6. All workflows reference this commit SHA for rule definitions

Example:
```
## Version History

- **v1.0** (2026-09-20): Initial two-model policy
- **v1.1** (2026-10-15): Increased Haiku quota threshold to 20 issues/week
```

---

## 13. APPENDIX: QUICK REFERENCE

**Model usage:**
- Haiku: Issue classification only
- Opus: Weekly diff audit only
- Auth: OAuth token via `claude setup-token`

**Weekly workflow:**
- Monday 9 AM: Generation (Tier 0)
- Sunday 4 PM: Audit (Tier 2)
- Sunday 5 PM: Digest email

**Quota target:** <10% of Pro weekly limit

**Escalation:** Anything ambiguous → human decision

**Kill switch:** `AGENT_ENABLED` repo variable

---

**End of GOVERNANCE.md**
