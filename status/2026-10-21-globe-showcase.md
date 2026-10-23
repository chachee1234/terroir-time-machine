# 2026-10-21 globe-showcase: G1 partly delivered by the owner; G3 still not started

## What ran
- `git fetch origin`; AUTOPILOT.md on origin/globe-showcase says `Autopilot: ON`. AGENTS.md is present (a later reminder that it was missing was wrong).
- New commits since the last run: 012247a (G1 script fix: `pygplates.reconstruct` output-list form) and eba0230 (owner commit adding `prototype/assets/plates/topologies.json`).
- Checked the committed topologies.json: valid JSON, ages 0–250 Ma in 1 Myr steps (251 frames), feature types ContinentalRift, MidOceanRidge, OceanicBasin, SubductionZone, Transform, Unclassified, 3.0 MB (under the 6 MB globe budget), Müller et al. 2019 credit and CC BY 3.0 licence in the file.
- First unchecked item: G3 (unblocked by owner on 2026-10-18).

## Result
- G1 stays blocked: its spec is 0–410 Ma, and the file covers 0–250 Ma only. Ticking it would overstate the export. The 250–410 Ma part still needs the owner's Mac run with the 410–250 Ma rotation file; the viewer wiring for topologies.json is also not built yet.
- G3 not started again. This is the second run that deferred it. The viewer change and its headless check are the work for the next run and should not be deferred again.
- No code change this run. Nothing merged, nothing pushed to main.

## Next action
- Next run: start G3 on the stylized showcase boundaries (`prototype/assets/plates/showcase_boundaries.json`, labelled "stylized"), then unit, browser and headless checks before ticking.
- Owner: running the Mac export for 250–410 Ma would complete G1.
