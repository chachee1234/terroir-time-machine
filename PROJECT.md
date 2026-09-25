# Terroir Time Machine

Version 1.0 · 2026-09-12 · Specification only

## Outcome and scientific promise
Build a free, open-source educational experience about the geological context and supported evolution of Mount St. Helena, California, spanning 1,000 Ma to present. A billion-year timeline is a narrative envelope, not a claim that the mountain existed for that entire interval or can be located throughout it. The experience must visibly change scale and evidentiary resolution through time.

Primary audience: curious Napa residents, wine visitors and educators. In five minutes, a visitor should understand the difference between global plate context, evidence for regional geological events, and the modern landform. They must be able to explain which images are measurements, reconstructions, illustrations or gaps.

## Current authorization
Produce planning documents, data contracts and acceptance specifications only. Do not scaffold an application, create a GitHub repository, run a development agent, acquire bulk datasets, provision services or publish. This package contains no application. Future development begins only on an explicit build instruction. This boundary is recorded in STATUS.md and AGENTS.md.

## MVP scope
- One subject: Mount St. Helena and enough northern Napa/Mayacmas context to interpret it. Do not confuse it with Mount St. Helens, Washington.
- Five chapters: deep-time global context; western North American regional context; Sonoma volcanic context and supported local units; landscape development and evidence gaps; modern terrain.
- A present-day terrain anchor, time/chapter navigation, play/pause, evidence panel, legend, sources page and shareable scene URL.
- At least one source-backed global plate view, one evidence-backed regional/local volcanic claim, one explicitly illustrative geological process animation and one measured modern terrain view. An evidence gap is a legitimate scene, but cannot replace all scientific content.
- Local AOI proposal: roughly 30 km square centered on the verified modern summit. This is a clipping/design extent, not a geological boundary. M1 must record an authoritative place identifier and coordinates before fetching terrain.
- All core content and render assets served from static files; no runtime AI, API keys, databases, accounts, analytics or paid map service.

Excluded: a Google Earth clone; a continuous photorealistic ancient Napa; parcel backtracking; exact ancient elevations, coastlines or eruption vents without evidence; soil formation simulation; modern farming/soil changes under 100 years; NDVI; wine-quality predictions; satellite imagery; other wine regions; voice generation; VR. NDVI describes recent vegetation, not deep geological history, and remains a possible later present-day overlay.

## Experience contract
Open on present-day terrain with title, location and Start journey. Chapters then run oldest to youngest. Header always shows age/interval, spatial scope and visual class. Evidence panel shows each factual claim, its sources and exact locators, limitations, confidence rationale, model/version and asset provenance.

Navigation uses discrete chapter stops with nonlinear spacing labeled “chapter spacing is not proportional to elapsed time.” Age decreases toward present; Ma means million years ago, 0 means the modern reference, not a simulated instant. No unsupported integer-year readout. Playback is presentation pacing, never geological rate. Within a chapter, only validated keyframes are selectable; unsampled ages show the bounding interval and interpolation label. Reduced-motion mode uses cuts and stills.

Deep-time mode uses globe-scale plate outlines or a gap card, no modern Napa pin. Regional mode uses published mapped extents or a schematic cross-section. Local mode appears only when claims support that scale. The modern locator returns only on modern terrain; any separate modern locator inset is labeled “present-day reference” and never implies an ancient coordinate.

Scientific content and visual styling live in separate records. Every scientific layer references a claim; aesthetic effects explicitly declare that they encode no additional scientific information. Unknown intervals fade through a labeled gap, never through invented terrain morphs. Mount St. Helena is not drawn as a generic intact cone by default.

## Proposed stack and cost contract
| Purpose | Selection | Constraint |
|---|---|---|
| Browser | TypeScript, Vite, Three.js, native HTML/CSS | Small dependency set; no UI framework unless a measured need emerges |
| Structured content | JSON, JSON Schema Draft 2020-12, Ajv | SCIENCE_RULES semantic validator supplements schema |
| Tests | Vitest and Playwright | Unit/semantic tests first; narrowly scoped browser checks |
| Offline preparation | Python, GDAL; QGIS only when inspection requires it | Clip and simplify once; cache by hashes |
| Plate reconstruction | GPlates/pyGPlates offline | Export a few model-derived keyframes; no browser scientific solver |
| Repository | Public GitHub repository | Created only during authorized development |
| Hosting | GitHub Pages project site | Free subdomain; static educational site, within current terms |
| Automation | Local checks and GitHub Actions | Deterministic CI, no paid model calls |

Three.js is MIT licensed [T01]. GPlates/pyGPlates are GPLv2 [T02]; keep offline tooling license notices and review distribution obligations separately from exported datasets. Each dataset retains its own rights. Project code target license: MIT. Original documentation target: CC BY 4.0; third-party materials remain under their licenses. Add actual license texts at M2, before publication.

$0 means no incremental service/API/domain spend, using existing hardware/internet and whatever included model allowance the user already has. It does not promise free labor, electricity, unlimited model usage or perpetual free hosting. If included model access is unavailable, pause model work; manual development and deterministic tools remain available. No API billing, paid trials, Codespaces dependency, Git LFS billing or automatic upgrade. GitHub is a proprietary service hosting an open-source project, not an open-source component. Pages currently permits public repositories on GitHub Free and has usage limits [T03]; recheck at M6. Scope and traffic must fit the free service. If not, stop publication and reduce assets or assess another free host with the user.

## Architecture and future repository layout
- This package's root documents: policy and current state.
- SCENES.schema.json: syntactic contract. SCENES.json: initial empty authoring manifest.
- evidence/sources.json: normalized source records from SOURCES.md; evidence/claims.json: claim records using the schema definitions; original citations retained.
- data/raw/: ignored local downloads; data/manifest.json: URLs, licenses, versions, CRS and hashes.
- tools/: reproducible preparation and semantic validation, created at M2/M3.
- public/assets/: licensed, clipped exports only, with provenance manifest.
- src/: scene resolver, evidence panel, renderer adapters, accessibility controls.
- tests/: semantic, unit and browser tests with the IDs in ACCEPTANCE_TESTS.md.
- .github/workflows/: checks and separate authorized static deployment.

Flow: source registration → claim review → asset derivation → scene validation → renderer. Renderer cannot synthesize scientific facts or bypass rejected claims. Keep presentation camera/timing separate from model reconstruction coordinates. Source changes invalidate dependent claims, assets and scene reviews by hash. A failed/missing asset yields a labeled gap and usable text; no substitute generated terrain.

## Data and performance budgets (targets, not measurements)
Initial transfer ≤3 MiB compressed; complete core tour ≤20 MiB; deployed site ≤50 MiB. Lazy-load per chapter. No individual committed asset >10 MiB. Initial mobile canvas ≤100,000 triangles; degrade to a static view if necessary. Target ≥30 fps in a recorded 30-second run on the declared M5 reference device, with controls remaining responsive. Cold load core controls ≤5 seconds at 10 Mbps and 100 ms latency. Browser GPU failure must preserve all science text. No service worker needed for MVP.

## Definition of done
M1–M6 acceptance gates pass; all published scientific claims have reviewed provenance; dataset rights and attribution verified; zero paid runtime dependencies; keyboard and reduced-motion paths pass; a clean clone reproduces the build and packaged assets within the documented tolerance; deployed commit matches tested commit. Do not call this a validated geological reconstruction until the recorded content review gate is satisfied. Owner signoff alone is not professional geological certification.

## Decisions and open risks
Chosen: constrained narrative, precomputed assets, a single renderer, no runtime AI, coarse-to-local evidence gating. Unresolved: local geological map/age reconciliation, exact data licensing, model version selection, scientific reviewer availability. Resolve these before local reconstructive animation; use an honest gap when evidence is absent. ROADMAP.md defines the execution order. SOURCES.md contains the source IDs above and the discovery record.
