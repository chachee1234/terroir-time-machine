## Globe showcase G0: planet-scale fixes, and the G0–G7 plan (2026-10-09)

Branch `globe-showcase`, from main 02b7ce8. Owner decision 2026-10-08: pause Napa/AVA detail and region work (AUTOPILOT R4 and D1–D3 marked "paused by owner"); focus on a whole-globe plate showcase. Not merged.

**What changed**
- `AUTOPILOT.md`: owner decision recorded; working branch is now `globe-showcase`; new queue G0–G7 with the owner's rules (visual-class label always on screen, globe additions under 6 MB, 60 fps on an M1 Air, headless check, tests, PR, status note); R4.3 and D1–D3 marked paused. Rules 2, 7 and 8 say "working branch" instead of `autopilot`.
- `prototype/timemachine.html` (G0):
  - The subduction block cut into the globe (SUB3D) is off by default, so nothing local shows at planet scale (it was visible at 84.5 Ma over Baja). The Plates chip still opens it. The 150 Ma chapter text now says "Press Plates to cut the globe open" (also in SCENES.json).
  - Plate names on the plate model are anchored at the middle of each plate's own present-day coastlines (`PM.cen`, rotated by the plate's Müller 2019 rotation), not at the stylized blob centres. Names are short (Laurentia/Baltica/Amazonia before 200 Ma, North America/Europe/South America after), hidden near the limb, and a name that would overlap another is dropped.
  - Timeline: colliding tick labels are hidden (current chapter wins, then the ends, then older first; 250/150 Ma at 960 px). Minor tick marks now sit on the same line as the others instead of at label height (they were drawn through "≈2.85 Ma").
  - Planet scale (older than the 27 Ma dive): only the Plates and Regions chips show (plus the scale and class chips); the Section and Places panels close. The compass, legend and Places panel sit under however many chip rows there are (`placeHud`, ResizeObserver), so the compass no longer covers Regions.
  - Between chapters on the globe the card shows a "the whole planet" line for that window (six windows, 1.8 Ga to 27 Ma, built into the page as `INTERLUDES`), labelled Reconstruction (stylized before 410 Ma, Müller 2019 after); the timeline caption reads "Meanwhile ...". A chapter stays up for a short hold after its tick (up to 3% of the run). Below 27 Ma (the dive and Napa) nothing changes.
- Daily routine: its prompt can only be changed from its own thread, so it was disabled (it would have run R4.3 Mendocino) and the new prompt was handed to that thread via the coordinator, to set and re-enable.

**Commands and results**
- `python3 scripts/validate.py`: PASS. `python3 -m unittest discover -s scripts -p 'test_*.py'`: 175 tests OK (3 skipped). `node tests/lint_js.mjs`: PASS. `python3 scripts/security_check.py`: PASS.
- Browser tests (`THREE_DIR=../three-r128 node --test --test-concurrency=1 "tests/browser/*.test.mjs"`): see the PR.
- Headless Chromium screenshots at 84.5 Ma (default view and over Europe/North Atlantic), 5 Ma (block) at 960×600, tick layout at 390/960/1440 px: no console errors, no missing files.
- 60 fps on an M1 Air: not measurable here (software WebGL); per-frame additions are a label loop over 8 plates and a class toggle. Owner check pending.
- Page weight: +about 6 KB of HTML; no new assets.

**Next smallest action**: G1, plate colours and boundaries. Needs the owner's OK to install pygplates on the Mac for the resolved-topology export.
