# 2026-10-24 globe-showcase: G3b1 sea-floor stripes (WIP, not ticked; browser suites pending)

## What changed
- `prototype/timemachine.html`: static sea-floor stripes beside every mid-ocean ridge in `topologies.json` (0–250 Ma), six per side, alternating light and dark, dropped where they reach a trench. `STRIPE` is exposed on the debug object.
- AUTOPILOT.md: G3b was split into G3b1 (static stripes, this step), G3b2 (animation), G3c and G3d (commit 3d98ebf).

## Checks run
- Lint (`node tests/lint_js.mjs`): PASS, 17 scripts parse.
- Headless screenshot at 100 Ma (`?debug&t=100`, swiftshader): stripes draw beside ridges, no page errors, 11648 vertices drawn.
- Browser suites (functional, integration, motion, security): RUNNING in the background when this was committed. Results unknown. Do not treat as passed.

## Not done
- G3b1 is not ticked until all four browser suites pass on this code.
- Stripes are static: no motion (G3b2).

## Next action
- Read the four browser logs, fix anything they show, then tick G3b1 in AUTOPILOT.md and update this note.

## Update 2026-10-28: browser results so far
- On the G3b1 code, before the environment reset: functional 25/25 pass, integration 2/2 pass, motion 5/5 pass. Security: 5 of 6 tests had passed on an earlier run; a re-run stopped partway (its log ends at test 5) and was not completed.
- This container has no three.js r128 copy and no access to npm or cdnjs, so the security suite cannot be re-run here.
- G3b1 stays unticked until the security suite passes on this code. Next run: re-run security (with a copy of three.js r128 in THREE_DIR), then tick G3b1.
