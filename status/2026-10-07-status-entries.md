## Progress notes move to `status/` — 2026-10-07
- Every open PR appended to the end of STATUS.md, so each merge re-conflicted the others (PR #39 conflicted twice on 2026-10-07). New rule in AGENTS.md and AUTOPILOT.md: each change writes its own `status/<YYYY-MM-DD>-<branch>.md`; STATUS.md keeps its earlier log and a pointer at the top. No script reads STATUS.md entries, so nothing else changes.
- Commands: `python3 scripts/validate.py` → PASS; `python3 -m unittest discover -s scripts -p 'test_*.py'` → all pass except the two numpy-dependent tests that cannot import numpy in this container.
- Next smallest action: owner decision; once merged, the next autopilot run writes its note here. Open PRs that already appended to STATUS.md keep working: they merge as usual.
