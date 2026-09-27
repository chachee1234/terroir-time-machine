# TTM Cinematic Roadmap (v2)

Goal: a finished Terroir Time Machine that plays one continuous shot from ~1.8 billion years ago to today for Mount St. Helena, ending on real modern terrain, and that can be re-run for a second location with new data but no new code.

Owner decision (2026-09-27): the experience may favor visual storytelling over strict scientific precision, as long as nothing breaks and every scene is labeled as stylized, illustrated or measured. This supersedes the "no fabricated scenes" rule for the viewer only; the evidence ledger (SOURCES.md, STATUS.md) keeps its rules.

## Where the project stands

- Strong: science ledger, GNIS + SIM 2956 intersection, real 3DEP terrain grid, Tier 0 scripts with 47 passing tests, gated workflows, accessible UI prototype.
- Weak: there is no experience yet. `SCENES.json` is empty, four of six prototype stops are "evidence gap" panels, and the only 3D content is one static DEM. The automation layer is ahead of the product.
- Rule of thumb from here: no new governance or workflow work until Phase 3 ships.

## Architecture (one idea)

Time drives everything. A single age value `a` (Ma) feeds pure functions that return every visual parameter: continent positions, terrain stage weights, sea level, sky, lava, ash, vegetation. Playback, scrubbing and chapter jumps only change `a`. Nothing is keyframed by hand in the renderer.

```
SCENES.json (chapters, ages, text, class)  ──►  state(a)  ──►  Globe scene  (a > ~180 Ma)
region terrain stages (S0..S5 heightfields) ──►            ──►  Local diorama (a ≤ ~180 Ma)
```

Local diorama = one GPU heightfield blended from six stages in the vertex shader:
S0 seafloor/trench → S1 accretionary islands → S2 uplifted Coast Range → S3 volcanic field + summit volcano → S4 caldera → S5 modern (real 3DEP).

## Sequential plan

Each step ends with something you can open and watch. Do them in order.

### Phase 1 — Cinematic prototype in the repo (1 session)
1. Add `prototype/timemachine.html` (this session's viewer). It already loads `prototype/assets/terrain.bin` automatically, so the final shot uses real USGS terrain when served from the repo.
2. Serve locally: `cd prototype && python3 -m http.server 8000`, open `localhost:8000/timemachine.html`.
3. Acceptance: plays start to finish at 60 fps on your MacBook Air; the last frame shows 3DEP terrain; no console errors.

### Phase 2 — Move content into data (1 session)
4. Fill `SCENES.json` with the 13 chapters (age, span, title, body, visual class). Extend `SCENES.schema.json` with `span`, `camera`, `scale` fields.
5. Viewer reads chapters from `SCENES.json` instead of the inline `CH` array. `scripts/validate.py` already checks age order; add a test for `span`.
6. Move plate keyframes to `data/plates/stylized.json`. Mark it `class: reconstruction-stylized`.

### Phase 3 — Real modern ground (1–2 sessions)
7. Raise the DEM grid from 224² to 512² and export a hillshade-friendly normal map (`scripts/fetch_terrain.py --out-cells 512`).
8. Drape SIM 2956 geologic units (already polygonized) as a color texture: Tswt, Tslt and neighbours. This was STATUS.md's next action; it becomes the "Today" layer toggle.
9. Add NAIP or USGS imagery as an optional "satellite" texture for the final shot (public domain).
10. Build S0–S4 as offsets from the real S5 instead of from procedural noise, so every era keeps the real valley layout.

### Phase 4 — CGI polish (2–3 sessions)
11. Sky: physically based atmosphere (Three.js `Sky` addon), sun angle per chapter, golden hour at "Today".
12. Water: animated normals, depth-based color, shoreline foam at S1.
13. Eruption: volumetric-looking ash (layered sprites + noise), pyroclastic flow sheet racing down the S3 flanks, lightning in the column, camera shake.
14. Erosion: animate drainage carving between S4 and S5 with a mask derived from real flow accumulation (`richdem` or `pysheds`, both open source).
15. Globe: replace blob continents with the GPlates-exported coastline polygons once a model's rights are cleared (Merdith 2021 is the target); until then, keep the stylized globe and its label.
16. Transitions: depth-of-field blur during the cloud dive; smooth scale bar that shrinks from 10,000 km to 30 km.
17. Audio (optional): wind, ocean, rumble, silence at the caldera, birds and vineyard ambience at "Today". Start only from a button.

### Phase 5 — Make it a product (1–2 sessions)
18. Vite + TypeScript build, vendored Three.js (already in `prototype/vendor/`), no CDN at runtime.
19. Evidence drawer: each chapter links to its SOURCES.md entries; stylized chapters say so plainly.
20. Performance budget: 60 fps on an M1 Air, 30 fps on a mid phone, < 8 MB download. Auto-lower grid to 256² on phones.
21. Deploy to GitHub Pages from `docs/` via the existing deploy script.

### Phase 6 — Region 002 (proves it generalizes)
22. Pick a location with a different story (e.g. Crater Lake, already issue #3).
23. Only new data: DEM, chapter list, stage heightfields recipe. Zero renderer changes. If code changes are needed, fix the abstraction before shipping.

## Design notes from the review

- Log time axis: 1.8 Ga to today on one slider, with the last 3 million years taking about 30% of the track. Linear time would make everything interesting happen in the last pixel.
- Event chapters hold and play their own mini-timeline (the caldera collapse runs 2.93 → 2.83 Ma over 7 seconds) instead of flashing by.
- Never pin today's summit on the ancient globe. The globe shows a glowing ancestral region (Laurentia, then its western margin). This keeps the project's core science rule while being fully cinematic.
- The block is shown as a museum-style cut slab with strata on its walls, which explains "what's underneath" without extra UI.
- Keep the visual-class chip on screen at all times. It is how the project stays honest while taking artistic license.

## Explicitly paused

- New workflows, digest changes, quota tuning.
- M1-06 datum transform (336 m from a contact is plenty for a 30 km cinematic view; revisit before any claim-level release).
