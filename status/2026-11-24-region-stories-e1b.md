# 2026-11-24 · region-stories · E1b viewer parent material

**Step:** E1b (the viewer half of E1; E1a is the data, on PR #66).

**Change:** `prototype/timemachine.html`:
- A fourth soil colouring, "Parent material", next to Series, Texture and Depth. Six plain classes plus "Not recorded" for units with no parent class (other regions have no parent-material data until their soil survey is built). Legend and share bars use the same palette.
- The section note says "Formed in …, on …" from the main soil's parent material and landform.
- The tour's soil summary has a "Formed in" share bar.

`tests/browser/functional.test.mjs`: the soil test also checks the new colouring's shares add up and that the button switches the legend.

**Checks run:**
- `node tests/lint_js.mjs`: 17 scripts parse.
- `node --test --test-timeout=0 --test-name-pattern="Soils chip|How it formed" tests/browser/functional.test.mjs`: 3/3 pass (the Soils chip test, the How it formed tour, and the gap strike-out test). The page loads with no errors in those runs.
- Not run here: the full browser suites (CI runs them on push).

**Next action:** E2 needs an owner decision (see status/2026-11-23-region-stories.md). Next run: S1 for Petaluma Gap, which needs the owner to check the Soils chip on the Mac.
