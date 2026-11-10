# 2026-10-20 globe-showcase: G3 still not started (second deferral)

## What ran
- `git fetch origin`; AUTOPILOT.md on origin/globe-showcase says `Autopilot: ON`.
- First unchecked item: G3, unblocked by the owner on 2026-10-18 (stylized showcase boundaries).
- Read the streak code: `MV`, `mvUpdate` and `put` in `prototype/timemachine.html` (about lines 506–565). The stylized era already drives per-continent streaks from `plateAt`; G3 needs ridge-to-trench streaks and convergence arrows on `prototype/assets/plates/showcase_boundaries.json`, which does not exist yet.

## Result
- No code change. The G3 build needs the new boundary file, a new viewer layer that is inside the 6 MB budget and the 60 fps rule, and headless checks of `timemachine.html`. That is more than this run could verify, so G3 stays unticked rather than shipping an untested viewer change.
- Unreviewed steps waiting on globe-showcase: 1 (G2). Nothing merged, nothing pushed to main.

## Next action
- Next run: write `showcase_boundaries.json` (five stylized boundaries, labelled "stylized"), add the G3 layer, then run the unit tests, the browser tests and a headless check of `timemachine.html` before ticking G3.
