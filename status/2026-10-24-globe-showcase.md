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
