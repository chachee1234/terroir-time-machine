## Globe showcase G2: Ocean toggle (branch `globe-showcase`) — 2026-10-13
- The queue's first unchecked item after G1 (blocked by the owner's Mac skip, 2026-10-11). G2 needs no pygplates, so this run did it.
- Added an **Ocean** chip (`#ocnBtn`, `OCN` in timemachine.html). When it is on, the globe's ocean colour blends with a depth-shaded seafloor. Depth comes from the globe's own relief texture (`prototype/assets/globe/relief.png`, negative heights; source Terrain Tiles, which carries NOAA ETOPO1 and USGS data, public domain; SOURCES already records this). Land is unchanged. Uniform `uOcean` is set in `apply()`.
- **Not a true transparent sea.** The globe is one opaque sphere, so the seafloor is drawn as shading under the water tint, not seen through it. The owner asked for "transparent sea"; if the true version is needed, that is a larger change.
- **Seafloor age colouring: not done.** It needs the EarthByte age grid, whose licence has not been checked, so it stays out.
- Tests: `python3 -m unittest test_export_plate_topologies test_build_share` → 10 run, OK. Full browser suite not run in this run.
- Headless check (swiftshader, `timemachine.html?debug&t=150`, Ocean on and off): the chip toggles, `aria-pressed` goes false → true, no page or console errors. Screenshots show the water patch change from dark navy to a lighter, olive seafloor tone. Caveat: the off and on shots were taken about 12 s apart, so some of the change could be camera motion; a clean check needs both shots with the camera fixed (the `cam=` option).
- Not checked: the 60 fps budget on an M1 Air, and the globe size budget (the change is a few lines of shader, no new data file).
- Next: G3 (motion from above: streaks ridge → trench and convergence arrows).
