# 2026-11-26 · region-stories · E3 blocked on an owner decision

**Step:** E3 (tour cues: each tour step opens the panel that explains it).

**Finding:** the plate section (`sd`, `sdToggle`, `plateAuto` idea) opens only when the viewer is on the 3D block (`SUB3D.local`). The Subduction (250 Ma), Seafloor (150 Ma) and Faults (28 Ma) chapters are at globe scale. Headless probe (`timemachine.html?t=0&debug`, tour started, Subduction step clicked, 12 s wait): the section stays hidden, no page errors.

**Tried:** a `plateAuto(c)` cue, modelled on `mbAuto`, called from `startDwell`, with a browser assertion. It did not open the section at globe scale, so both edits were reverted. Nothing was committed for E3.

**Owner decision needed:** (a) the tour dives to the block for these three steps, or (b) the plate section can open from the globe as a side panel. Recommendation: (a), since the block is what the section draws.

**Next action:** E4 (block colours) is independent of E3 and can run next; E3 waits for the decision.
