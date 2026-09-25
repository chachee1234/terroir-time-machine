# Scene data contract

SCENES.schema.json is the JSON Schema Draft 2020-12 contract for SCENES.json. The supplied manifest is intentionally empty in authoring mode: no research has been promoted into production scenes. Do not mistake an empty valid manifest for a releasable tour.

The manifest embeds compact source, claim and asset tables plus scenes. Future authoring ledgers contain fuller bibliographic metadata; a deterministic exporter creates this runtime subset. Each scene separates scientific properties from its presentation object. Use `python-jsonschema` for specification validation or Ajv 2020 for the future TypeScript validator. Enable format checks and strict mode where applicable.

## Semantics that JSON Schema does not prove
Implement at M2 and require in release builds:
- Unique IDs across each table, resolved references, no duplicate scene IDs.
- Older age ≥ younger age; frames oldest-to-youngest and inside scene interval; scene sequence ordered oldest-to-youngest with explicit gap coverage from 1000 to 0. Editorial windows are not event dates.
- Frame scientific claims cover the represented time/scope, assets and model inputs. Do not require a narrowly dated claim to cover an entire editorial window; unclaimed portions display gaps. Reconstruction is never silently extrapolated.
- Release manifest nonempty and satisfies minimum scientific views in PROJECT.md. Release rejects any pending/rejected scene or referenced claim, candidate/metadata-only science source, unresolved/prohibited asset rights, or missing reviewer/date/scope. Unpublished candidate records may exist only in authoring ledgers.
- Approved local reconstructive geometry has a real qualified reviewer and scope matching the geometry; a string or schema approval flag cannot establish credentials.
- Labels correspond to visual classes, datum/epoch are meaningful, all model/input provenance is present. Model interpolation uses compatible same-model frames and never bridges an unknown interval.
- Scientific assets have supporting claims. Aesthetic assets cannot covertly encode unsupported scientific geometry. Claim IDs in assets/frames must be attributable through the active scene.
- Referenced files exist, are packaged locally and match SHA-256/byte counts. Attribution and rights are valid; model and asset source rights are independently checked. Source links may be remote; render asset paths may not be.

These checks supplement manual science review. Schema constraints deliberately permit pending reviews during authoring; only release validation admits approved material. The non-local anchor rule is conservative: no ancient scene receives a modern point even where future scholarship might justify one. Changing this policy requires explicit scientific design review, never an agent convenience edit.

No schema field contains a fabricated ancient coordinate. Modern local_anchor is optional and allowed only at time 0; it requires an authoritative place source. Renderer camera orientation is not a georeferenced ancient location. `modern_data_epoch` records the actual source epoch string after verification.
