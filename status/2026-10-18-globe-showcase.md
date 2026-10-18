# 2026-10-18 globe-showcase: G7 blocked (licence unconfirmed)

## What ran
- `git fetch origin`; read AUTOPILOT.md from origin/globe-showcase (`Autopilot: ON`).
- Queue check: G1 blocked (owner), G2 done (PR #54, unreviewed), G3–G6 blocked. G7 is the first unchecked item.
- WebSearch: "Merdith 2021 plate model 1 Ga licence Zenodo GPlates rotation files CC BY".
- WebFetch of the EarthByte README for Merdith 2021: no licence or citation terms stated. It limits use to 5 Ma and longer timescales and says not to use it for Pacific analysis or hotspot motion.
- WebFetch of zenodo.org/record/13798790 (v2.0.0): rejected by the proxy with HTTP 429. The licence on that record is unverified.

## Result
- No licence confirmed for the 1.8–2 Ga model, so nothing was added to the viewer or to SOURCES.md.
- G7 marked [!] blocked. The owner needs to confirm a licence (or pick another published model) before any addition.
- No code, data or page changes beyond AUTOPILOT.md and this note.

## Not run
- Headless and unit checks: no page was changed, so none were run.
- The Zenodo licence check needs a retry later, after the rate limit clears.

## Next action
- Owner: confirm the Merdith et al. 2021 Zenodo licence, or pick another 1.8–2 Ga model whose licence is stated.
- Routine: nothing further until the owner answers. G3–G6 still wait on the G3 decision card (wait for G1, or stylized-only).
