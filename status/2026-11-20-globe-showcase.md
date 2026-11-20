# 2026-11-20 globe-showcase: G3b2 moving sea-floor stripes

## What changed
- `prototype/timemachine.html`: the G3b1 stripes now move. Each ridge vertex is stored once per stripe slot with the ridge direction (`aTan`), its slot (`aJ`, signed by side) and how far its sea floor can travel before a trench (`aLim`). The vertex shader rotates it across the ridge by `(slot - 1 + uPh) × 0.7°`, so stripes spread outward, a new one fades in at the ridge and the outermost fades out; a stripe fades to nothing at its trench. Only `uPh`/`uPar` change per frame; the geometry is rebuilt only when the age changes (same cost as G3b1: 16 ms at 30 Ma in headless swiftshader).
- Speed: `uPh` advances at 0.25 × camera height per second (clamped), so the stripes cross the screen at about the same speed at any zoom. Not to scale. With reduced motion they stay still at the G3b1 positions.
- `tests/browser/motion.test.mjs`: new test for the motion, the trench clip and reduced motion.
- AUTOPILOT.md: G3b2 ticked, and G3b1 ticked: all four CI gates passed on PR #60 (merged 2026-11-20 as 2fd3002), browser 47/47, which carries the G3b1 code. PR #60 also pinned the browser job to ubuntu-24.04 and made two timeout-prone tests click through the DOM.

## Checks run
- `node tests/lint_js.mjs`: PASS.
- New motion test alone: PASS. Headless screenshots at 100 and 30 Ma: stripes draw and move, no page errors.
- Full suites: see the PR checks.

## Not done
- 60 fps on the owner's M1 Air: pending owner check.

## Next action
- G3c: motion arrows and transform offsets.
