## Animation polish, technical-artist pass (2026-10-09)

Branch `animation-polish`. Owner request: "use Unreal Technical Artist to enhance animation". The Unreal Technical Artist role from msitarzewski/agency-agents (game-development/unreal-engine) was read as a review lens only: its material, VFX-budget, LOD and profiling rules applied inside three.js r128. No engine change, no plugin or hooks. The globe animation is untouched (PR #46 owns that area). Not merged.

**What changed (all in `prototype/timemachine.html`, all aesthetic)**
- Camera: the ground camera follows a critically damped spring (SmoothDamp) instead of an exponential lerp, so chapter changes ease in as well as out, and the end of the dive hands its speed to the follow instead of stopping dead. User control or a region flight resets it to rest.
- Relief shading: per-stage occlusion computed once on the CPU from the stage heights at ≈1 km and ≈4 km (`CAV`, attributes `aCavA`/`aCavB`, blended with the same weights as the heights). Valleys get less sky light, ridges a little more, plus a faint warm bounce light. Close-ups sample the same grid. Meshes without the attributes read 0, which is neutral.
- Aerial perspective: haze is a little thinner on high ground and glows warm when looking toward the sun.
- Eruption: ash puffs are lit as soft spheres from the sun, with lumpy edges, glow orange low over the vent, slow at the top and spread into an umbrella cloud; in the caldera eruption about 15% roll down the cone as pale surges (the chapter text already describes ash flows; shapes invented, chapter stays labelled Illustration). Firelight from the vent on the nearby slopes. A short decaying camera shudder when the caldera eruption starts (never with reduced motion, only while the camera is automatic). Budget 3,200 points (600 with reduced motion), was 2,600.
- Frame-time budget: if frames run slower than about 38 fps for a few seconds, the renderer drops the pixel ratio in 0.25 steps (not below 1 CSS pixel); it climbs back when there is headroom, never above the level that was too slow.
- Soft vignette over the 3D view (CSS, under the UI).

**Commands and results**
- `node tests/lint_js.mjs`: PASS. `python3 scripts/security_check.py`: ok. `python3 scripts/validate.py`: PASS. `python3 -m unittest discover -s scripts -p 'test_*.py'`: 175 tests OK (3 skipped, as on main).
- Browser suite: see the PR.
- Before/after stills (headless Chromium, fixed camera via `?t=…&cam=…`): `/mnt/project-files/cinematic-viewer/polish-*.png` in the project files.

**Next**
- Owner review of the look. Possible follow-ups: soft shadows from a depth pre-pass, flow-mapped river shimmer on the NHD layer.
