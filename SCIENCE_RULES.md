# Scientific evidence and visualization rules

Normative. If visual ambition conflicts with these rules, reduce visual precision or show a gap. A passing schema is not scientific approval.

## 1. Four visual classes
| Class | Meaning | Required visible label |
|---|---|---|
| measured | Representation of observations or mapped data, with resolution limits | “Measured/mapped data · [epoch]” |
| reconstruction | Output of a named scientific model constrained by evidence | “Model reconstruction · [model/version]” |
| illustration | A mechanism or qualitative interpretation; shapes and motion are not recovered history | “Illustrative process · geometry and timing are schematic” |
| gap | Evidence does not support this view | “Local reconstruction unavailable for this interval” |

Claims separately use observed, interpreted or modeled. Confidence is high, moderate or low with a written reason, not an invented probability. Visual realism, fine mesh spacing or smooth playback never increases confidence. Public reconstructions need reviewed claims; draft placeholders cannot ship as fact.

## 2. Identity, scope and time
Verify Mount St. Helena, California using modern authoritative mapping. Reject Mount St. Helens/1980 eruption material as local evidence. Source coverage must encompass the claimed locality and age. A volcanic field-wide age range is not a summit eruption date. A sample date is not the time a mountain acquired its present shape. A present rock unit does not identify its exact ancient location.

Use Ma, positive into the past, with older_ma ≥ younger_ma and domain 0–1000. Published errors retain their units, statistical meaning and source precision. Narrative chapter boundaries are editorial and must not be described as event dates. Dates with no supported uncertainty state “uncertainty not reported”; do not infer a distribution. Source publication year and dataset survey epoch are separate from geological age.

## 3. Forbidden precision
- No tracking a modern summit, parcel or Napa coordinate back to 1 Ga. A plate assignment is not proof that today's local crust existed on that plate at that age.
- No reconstructed parcel boundaries, ancient vineyard soils, exact ancient drainage, vents, coastlines or elevations from present DEMs.
- Plate polygons are not shorelines; rotations do not reconstruct topography. Ancient absolute paleolongitude may be model/reference-frame dependent; display that limitation when applicable.
- No assumed modern landform before evidence supports it; no automatic cone, caldera or lava flow footprint assigned to Mount St. Helena.
- No exact erosion/uplift/displacement rates inferred from two pictures. No interpolating unconnected geological episodes into apparent continuous history.
- No numerical uncertainty radius invented to make a weak reconstruction look quantified. No modern terrain vertically scaled backward as a reconstruction.

The deep-time global tier has no local anchor regardless of zoom. Local reconstructive geometry requires a claim specifically supporting its geometry and interval; one citation about regional volcanism is insufficient. A conceptual cross-section may be animated without geographic coordinates but must remain visibly schematic.

## 4. Evidence admission
Every claim needs a stable ID, precise assertion, scope, age interval, evidence class, confidence rationale, supporting source IDs and page/figure/table/map-unit locators. Capture conflicting evidence and limitations. Use primary geological surveys, peer-reviewed work and author-deposited datasets. Search snippets and model memory are discovery aids only. Abstracts support only statements made in those abstracts; they cannot approve unseen figures or precise local geometry.

Source verification levels: candidate, metadata_verified, content_verified. Publication eligibility requires content verification at the scope actually used, and review of every claim. Do not treat a catalog page as review of the underlying map. Asset redistribution requires an explicit compatible license/rights basis; public download access is insufficient. Record rights separately for paper text, figures, GIS data and software.

For incompatible dates, inspect sample locality, unit definition, dating method, uncertainty, calibration and later work. Preserve both records; do not average or silently replace them. The 1972 and 2011 Sonoma records in SOURCES.md illustrate scope differences to resolve, not permission to use either range as the mountain's lifetime.

## 5. Evidence/presentation boundary
Science records own assertions, temporal support, geometry provenance, uncertainty and review. Presentation records own camera, colors, playback seconds and aesthetic effects. Every layer declares semantic_role: scientific or aesthetic. Scientific layers reference reviewed claims. Aesthetic layers carry no apparent scientific motion/location information. Scientific and aesthetic geometry never share an unlabeled visual convention.

Named model output records model version, reference frame, reconstruction age, input feature IDs and processing recipe. Use discrete model-derived keyframes; interpolation between independently compatible frames may be labeled model interpolation, never observation. Cross-model changes require a visible cut and model change notice. A cinematic transition can move a camera but cannot imply migration of the mountain.

## 6. Modern terrain and terroir
Record source horizontal/vertical CRS, units, cell size, survey epoch and transformations. Resampling does not improve accuracy. Display vertical exaggeration if not 1; default 1. Verify summit/landform orientation against an independent authoritative modern map. Geologic map scale governs interpretation: zooming cannot create parcel accuracy.

Bedrock, parent material, transported deposits and present soils are distinct. No one-to-one claim that volcanic rock determines a vineyard's soil or wine flavor. Modern imagery/NDVI cannot reconstruct ancient geology. Any future soil layer needs its own spatial and interpretive uncertainty, outside this MVP.

## 7. Release gate and fallback
A maintainer reviews citations and claim-to-visual correspondence. Reconstructive local geometry additionally needs documented review by a qualified geoscientist; if none is available at $0, omit that geometry and use reviewed limited claims plus schematic processes/gaps. Do not fake reviewer credentials. An AI review is a consistency aid, never independent expert approval.

Reject or disable a scene with missing citations, inconsistent time order, unresolved rights, unreviewed scientific claims, unsupported local anchors or decorative assets posing as evidence. Unknown remains unknown. Status must record rejection and the safe fallback. No autonomous agent may mark its own research as expert-verified or weaken acceptance tests to ship.
