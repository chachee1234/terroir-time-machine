# 2026-11-10 · formation-and-soils

Charlie asked for a review of the automations, code and animations, and edits "for faster progress, better look and educational animations", with this end result: each wine region has a clear visual of how it formed and of its soil composition.

## What was found
- **Autopilot:** no step landed between 2026-10-28 and 2026-11-10. It was stopped on one browser suite it could not run (no three.js r128 in the cloud container). The routine's prompt also reads this queue from `globe-showcase`, which is now a merged, stale branch.
- **CI on `main` is red** (run 42749341898): one motion test timed out in `page.click("#next")` at Playwright's 30 s default while the page was busy under software WebGL. The same test passes here in 88 s. Every other browser test in that run passed.
- **Distance to the goal:** only the Napa–Sonoma frame has geology, soils and formation chapters. Petaluma Gap, Northern Sonoma and West Sonoma Coast have five or six chapters each listed as gaps and no soils or geology; Mendocino has no live page. The globe queue (G3b2–G9) does not close any of that.
- **Look, from headless screenshots:** today's views are strong. Before today the ground is a flat green slab with fault lines in every region and the caldera eruption is a few pixels wide; the globe's land is one flat colour; the soil map by series is 95 unrelated colours; at 150 Ma the Plates cut-away drew as a plain brown box (software WebGL, to be checked on a real GPU).

## What changed
- `prototype/timemachine.html`
  - **"How it formed" chip:** a guided tour of the region's own chapters as numbered steps (Subduction, Seafloor, Faults, Volcanoes, Volcano, Caldera, Valleys, Soils), with Back, Next and End tour in the card. Works for every region. A step the region's `scenes.json` lists under `gaps` is struck out and shows the file's reason. No new geological statements: the text is the chapter's.
  - **Soil summary on the last step:** share of the surveyed frame by topsoil texture and by depth to rock or a root-limiting layer, and the six most widespread soil series with a sand/silt/clay bar, texture and depth. From `soils.json` (USDA SSURGO map-unit averages). A region without a survey says so.
  - **Soil map colourings:** Series (as before), Texture and Depth, switched in the legend.
- `tests/browser/harness.mjs`: page default timeout 180 s, so a click on a busy page does not fail at 30 s. Each test keeps its own overall timeout. No assertion was changed.
- `tests/browser/functional.test.mjs`: two tests for the tour (Napa, and a region with gaps, read from its data files).
- `AUTOPILOT.md`: new first-priority queue "Region stories" (engine steps E1–E7, then soils, geology, formation chapters and a check for each region); up to three steps per run; CI is read at the start of each run and runs the full browser suites; the routine runs only the tests for what it touched; working branch `region-stories`; review cap 12 steps; G3b1 ticked on CI evidence; Globe showcase is second priority.
- `README.md`: the tour and the soil colourings.
- Includes the commit from PR #60 (three.js r128 in `tests/vendor/`), which this work needed to run browser tests.

## Checks run here
- `python3 scripts/validate.py`: PASS. `python3 -m unittest discover -s scripts -p 'test_*.py'`: 210 tests OK (2 skipped). `node tests/lint_js.mjs`: PASS. `python3 scripts/security_check.py`: PASS.
- Browser (Chromium headless, software WebGL): see the PR for the list that was run. The full suites were not run here; CI runs them on the PR.
- Screenshots of the tour (desktop and 390 px wide), the soil summary and the Depth colouring were looked at.

## Not done, not tested
- 60 fps on the M1 Air, and the tour on a real phone: owner check.
- No new data: this container cannot reach Soil Data Access or USGS, so no region gained soils or geology here. Those are the S1 and S2 steps.
- The look problems listed above are queued as E4 and E5, not fixed.

## Next action
- Owner: merge the PR, then update the routine's prompt (text in the PR description) or delete the merged `globe-showcase` branch so the routine reads `AUTOPILOT.md` from `main`.
- Routine: E1, then E2, then S1 Petaluma Gap.
