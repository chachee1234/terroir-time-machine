# 2026-10-22 globe-showcase: G3a boundary lines (not ticked; tests pending)

## What changed
- `prototype/timemachine.html`: G3a draws the moving boundaries from `prototype/assets/plates/topologies.json` (0–250 Ma): ridges as double lines, trenches, rifts and transforms in their own colours. Nothing is drawn before 250 Ma. `TOPO` is exposed on the debug object.

## Checks run
- Lint (`node tests/lint_js.mjs`): PASS, 17 scripts parse.
- Headless screenshot at 100 Ma (`?debug&t=100`, swiftshader): boundary lines draw, no page errors, 4068 vertices drawn.
- Browser suite (`node --test tests/browser/*.test.mjs`, three r128 from a local copy): NOT FINISHED. The functional file was still running after about 30 minutes under software WebGL. Result unknown. Do not treat as passed.

## Not done
- G3a is not ticked in AUTOPILOT.md until the browser suite passes.
- Trench teeth and dashed transforms are not in this step.
- G3b–G3d, G4, G5, G6 untouched.

## Next action
- Re-run the browser suite per file (`THREE_DIR` pointing at the local r128 copy), fix anything it shows, then tick G3a.
