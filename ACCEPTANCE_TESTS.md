# Milestone acceptance tests

These are executable-intent specifications, not a claim that application tests exist. M0 schema checks are the only executed tests; see VALIDATION.md. At M2 implement semantic/unit tests; browser tests arrive at M4. A gate fails if any required case fails. Every result records task ID, commit, command, environment and output artifact. Scientific review remains a human content gate.

## M0 — specification
- S00: All requested files exist; no application source, live CI or deployment is created. PASS requires PROJECT, SCIENCE_RULES, ROADMAP, SOURCES, SCENES.schema.json, SCENES.json, STATUS and this test specification.
- S01: Draft 2020-12 meta-validation passes; SCENES.json validates as an empty authoring manifest. Empty must fail the future release semantic gate.
- S02: A minimal valid gap fixture passes; extra fields, missing labels, out-of-domain ages and a local anchor in global context fail schema validation.
- S03: Documents distinguish $0 incremental spend from unlimited model access, and specification status from completed software. Manual review.

## M1 — evidence and feasibility (human + ledger checks)
- E01: Verify the place is Mount St. Helena, California. Deliberately substitute a Mount St. Helens, Washington reference; local-source admission must fail.
- E02: Every proposed public claim has content-verified supporting material with precise locator and appropriate scope. An abstract-only reference cannot approve a figure it does not reproduce.
- E03: A field-wide Sonoma age range cannot pass as a summit eruption date. Reject that fixture; accept a narrowly worded field-level claim with limitations.
- E04: Every proposed distributable dataset has explicit rights and version. A publicly downloadable file with unresolved license must fail asset admission.
- E05: No local point or terrain for 1000 Ma. A global model may pass with no local anchor and an explicit limitation; “Napa was here” fails.
- E06: Storyboard covers 1000 Ma to modern, including gaps, and has feasible inputs for global model view, modern terrain, a regional/local volcanic claim and schematic process. Missing all local scientific evidence fails M1.
- E07: Reconcile conflicting dates or narrow/withhold claims. No fabricated expert review. Local reconstruction remains disabled without the required review.

## M2 — contracts (automated)
- C01: Validate manifest and every scene against schema; reject unknown fields and invalid enum values. Empty/draft is authorable but cannot release.
- C02: Resolve IDs across scene, claim, source and asset tables. Duplicate IDs, dangling refs or unsupported source status fail. Unreferenced candidate ledger records may remain unpublished.
- C03: Check older ≥ younger, source/claim support for each scientific frame's age and spatial scope, and frame ordering. A claim covering 3–2 Ma cannot back a 7.5 Ma frame.
- C04: Reject ancient local-anchor coordinates, wrong scope and unreviewed local reconstructive geometry. Reject measured class for ancient scenery. A modern measured scene needs data epoch and CRS provenance.
- C05: Every scientific asset has at least one reviewed claim and attributable rights. Every scene label matches class. Reclassifying unsupported geometry as aesthetic while it conveys location/time must fail manual review.
- C06: Missing file, traversal path, unapproved remote asset URL, checksum mismatch and unresolved rights fail build validation. A gap with no assets and clear limitation passes.

## M3 — data preparation (automated + visual)
- D01: Clean reproducible preparation from pinned input hashes produces identical outputs, or documented floating-point tolerance with fixed tool versions. A changed input hash invalidates cached output.
- D02: DEM test: known source samples transform to output within the declared resampling tolerance; units and vertical datum preserved or correctly transformed. Reject swapped axes or meters/feet mismatch. No-data does not turn into artificial zero-elevation pits.
- D03: Modern terrain orientation, location and landmarks checked against independent authoritative mapping. Render limits do not claim finer source accuracy.
- D04: Global frames at 1000 Ma and one younger supported age match the chosen model's own export within documented simplification tolerance. Verify antimeridian handling. No modern summit anchor or implied coastline.
- D05: Schematic process shows its label throughout playback. No coordinate scale, unsupported vent location or numeric erosion rate; evidence panel names what is schematic.
- D06: Asset budgets in PROJECT.md pass; core assets are locally packaged, rights notices included. A broken asset results in an explicit gap, not invented substitute scenery.

## M4 — interaction and access (browser)
- U01: Start, play, pause, previous/next chapter and evidence toggle work with keyboard and touch. Paused scene stops all nonessential motion; focus is visible and retained.
- U02: Going oldest→youngest never increases displayed geological age; 1000 and 0 endpoints reachable. Nonlinear navigation label always accessible. Arbitrary intermediate age displays a supported interval/gap, not fake precision.
- U03: At every transition, visible class, age and limitations match the displayed geometry; no stale local pin persists when switching to deep time. Evidence panel references the active scene only.
- U04: Reduced-motion preference disables continuous animation. WebGL failure leaves complete readable narrative, sources and navigation. Color is not the only confidence/class cue.
- U05: Scene URL survives reload and project-subpath hosting. Unknown ID falls back safely to introduction with a clear notice. At 390×844 and 1440×900 there is no control overlap or horizontal text clipping.
- U06: Sources are accessible links with exact claim locators; touch targets ≥44 CSS px and normal text contrast ≥4.5:1. Missing/corrupt content produces a useful error, never a blank screen.

## M5 — review and hardening
- Q01: Release validator rejects empty manifests, pending/rejected scenes, unsupported assets and unresolved rights. Production uses only reviewed eligible content.
- Q02: Manual side-by-side audit of every claim and geometry against its sources passes. Reviewer identity/scope/date recorded. Local reconstructive geometry requires qualified geoscientist signoff; otherwise omit it.
- Q03: Measured transfer, cold-load and frame-rate budgets pass under PROJECT.md conditions. Save browser/device/version and measurement method; do not report targets as results. If performance fails, reduce complexity and rerun only affected checks.
- Q04: Browser smoke in Chromium, Firefox and WebKit passes; at least one real mobile check or explicit remaining release blocker. No uncaught errors, runtime keys, tracking or required third-party network calls. Blocking outbound requests except site origin preserves core tour; external source links may require internet.
- Q05: A first-time reader can identify one measured view, one model output, one schematic and one unknown, and understands ancient Napa's exact location is not supplied. Record comprehension issues and fix misleading labels.

## M6 — release
- R01: Clean clone, locked install, validation, tests and static build all succeed. No secrets, unlicensed assets or bulk raw data committed.
- R02: Review current hosting terms/quotas, verify $0 plan and educational use; no payment method, paid service or custom domain required. Exceeding free limits blocks release.
- R03: Owner's publishing authorization and tested commit recorded. Deployed bytes derive from that same commit; subpath assets and direct scene links work on live host.
- R04: About page includes scope/limitations, license notices, model version, data epochs, attribution and content revision. No unsupported “scientifically proven” marketing.
- R05: Rollback documented and demonstrated in a nonproduction check using a previous artifact or commit; STATUS records live URL/SHA only after successful deployment verification.

## Future check command contract
Define scripts at M2: `npm run validate:content`, `npm run test:unit`, `npm run build`; at M4: `npm run test:smoke`; at M5: `npm run check:release`. These names are planned interfaces, not runnable commands in this package. Offline data preparation is a separate explicit command and never triggered by browser visits. Test failures must be fixed or block the milestone; do not edit expected results to match unsupported output.
