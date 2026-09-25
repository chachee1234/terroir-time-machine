# Roadmap and autonomous execution framework

Specification version 1.0. Development is not started. Milestones execute sequentially; no model swarm or background loop. Acceptance IDs refer to ACCEPTANCE_TESTS.md. Estimates are planning ranges of focused human/tool work, excluding waits and unavailable evidence, not promises.

| Milestone | Dependency | Deliverable | Acceptance gate | Estimated work |
|---|---|---|---|---|
| M0 Specification | none | This package and validated schema | S00–S03 | complete at document level |
| M1 Evidence feasibility | explicit build authorization | verified place, source/claim ledger, rights, 5-chapter storyboard | E01–E07 | 4–8 hours; stop if local evidence unavailable |
| M2 Contracts and skeleton | M1 | minimal app shell, validators, fixtures, pinned tooling, licenses | C01–C06 | 2–4 hours |
| M3 Static science assets | M2 | clipped modern terrain, plate keyframes, process illustration, manifests | D01–D06 | 4–8 hours |
| M4 Tour and evidence UI | M3 | controls, renderer, narrative, accessible evidence panels | U01–U06 | 4–8 hours |
| M5 Review and hardening | M4 | evidence audit, browser/performance report, repairs | Q01–Q05 | 2–6 hours plus reviewer time |
| M6 Static release | M5 and publish authorization | reproducible GitHub Pages release | R01–R05 | 1–2 hours |

## M1 storyboard targets; ages are editorial windows
1. 1000–250 Ma: global plate context using one licensed model, explicitly not local Mount St. Helena reconstruction. If model rights cannot be verified, hold M1 and find an open alternative; no invented continent maps.
2. 250–10 Ma: regional context where reviewed sources support it, otherwise an evidence-gap panel. No assumption that one source covers this entire window.
3. 10–2.5 Ma: investigate Sonoma volcanism and local mapped units. This window is not a claim that Mount St. Helena formed at 10 Ma. Separate field-scale chronology from local dates.
4. 2.5–0 Ma: investigate landscape modification; show only dated/supported episodes, a schematic process, or a gap. Do not invent continuous uplift or erosion rates.
5. 0 Ma: measured/mapped modern terrain and geological context. Modern is the data epoch, not real-time sensing.

Windows support navigation only. Each eventual scene has its own evidence-bounded time range; gaps must cover unsupported intervals. Final manifest includes both endpoints without requiring false continuous geometry. The illustrated process belongs to a chapter only after relevant process claims are reviewed.

## Task unit and model policy
Default to deterministic scripts, grep/ripgrep, diffs and targeted tests; use no model for downloading, hashing, conversion, formatting, builds or repeatable validation. Use the least expensive capable model already included in the user's access for bounded implementation. Escalate one narrow task to a stronger reasoning model only for unresolved evidence conflicts, architecture risk or two failed repair attempts. Model names and allowances vary; pin the selected available model once in STATUS.md when development starts, rather than repeatedly browsing pricing or assuming any named model is free. No API-funded runner.

A task changes one coherent concern, normally ≤3 files and ≤200 changed lines; larger cohesive work must explain why splitting increases risk. Read AGENTS.md and STATUS.md, then only the task-relevant contract and code. Do not reload the whole repository, raw papers or conversation. Source extracts should be saved as short claim-specific notes with locators, within redistribution rights.

Targets per ordinary model task: ≤6,000 input tokens, ≤1,500 output tokens; cap the work packet at 800 tokens and handoff at 250 words. These are routing targets, not reasons to truncate necessary evidence or valid files. Record actual usage when the runtime exposes it; otherwise mark estimated/unknown. Avoid generating verbose code explanations, repeated plans and duplicated document summaries. Emit patches and a short result.

## Bounded autonomous loop
State transitions: READY → IN_PROGRESS → VERIFYING → DONE, or BLOCKED. One task at a time, one checkpoint per completed task.
1. Read current state and inspect git status. Preserve unrelated user changes. Select the earliest unblocked task whose prerequisites passed.
2. Define task ID, acceptance IDs, allowed files, necessary inputs, deterministic commands and stop conditions. Save to STATUS.md before changing code.
3. Make the smallest patch. Run only the relevant checks; run the full milestone gate once at completion or when shared behavior changes.
4. If a check fails, inspect the specific output and allow at most two repair attempts. Then checkpoint as BLOCKED with evidence and one concrete next action. Never repeat an identical failing tool call or weaken a test.
5. Update STATUS.md with task result, commands/exit codes, changed files, source hashes affected and next task. Commit to the working branch when repository authorization permits; no force-push, secret handling shortcuts or unrelated changes.
6. Continue to the next ready task only within the authorized session budget. At quota/time exhaustion, stop cleanly with a resumable handoff. Never claim that work continues after the session ends.

Budget default: one milestone or 60 minutes of agent runtime per authorized run, whichever comes first; no scheduled retries. This does not schedule a job. A future user can change the budget explicitly. Repeatable CI may run on pushes/PRs after repository setup, but it executes tests, not a self-calling model.

## Escalation and publication boundaries
Proceed autonomously on reversible implementation within the authorized milestone. Stop for unresolved scientific claims that would change meaning, unknown redistribution rights, new spend, unavailable credentials, or publication without authorization. Resolve uncertainty with reduced scope where permitted; do not ask the user to decide geological truth. Record the specific blocker. Publishing must be the final action after a tested artifact is reviewable.

No default unattended LLM through GitHub Actions, no polling ChatGPT, no API-key workaround. True unattended model development is not guaranteed at $0. A user-started included session can do bounded work; deterministic CI can continue independently. No workflow is installed by this specification.

## Future CI contract
On a PR: dependency install from lockfile, schema/semantic validation, relevant unit tests, build; browser smoke only for UI/shared code changes. Cache dependencies by lockfile and generated assets by source/recipe hashes. Data preparation runs only when inputs change; never fetch mutable science assets during deployment. Use concurrency cancellation for obsolete runs and least-privilege workflow permissions. Deploy workflow runs only after explicit release authorization on a tested commit; record published SHA. Do not enable scheduled model jobs.

## Work packet template
Task ID / milestone:
Goal and acceptance IDs:
Read only:
Allowed files:
Evidence inputs and hashes:
Checks:
Budget and stop conditions:

## Resume prompt (for a later authorized build session)
“Read AGENTS.md and STATUS.md. Continue the earliest ready task in ROADMAP.md within the stated budget. Read only necessary files. Preserve SCIENCE_RULES.md. Use deterministic tools first and included model access only. Do not publish unless already authorized. Stop after two failed repairs or an evidence/rights blocker. Update STATUS.md with actual checks and the next action.”

## Cut order if cost or scope slips
Remove polish → reduce geometry/frames → remove optional local geometry → retain schematic/gap treatment. Never cut citations, limitations, accessibility basics, evidence validation or rights checks. If the minimum scientifically supported tour cannot be assembled, report a feasibility failure instead of shipping invented history.
