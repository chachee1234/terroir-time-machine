# Hand-off queue (Workflow H)

When Claude plans work, it splits it into small task cards here, one JSON file per card in `queue/cards/`. Each card says whether a free model may draft it (L1) or only Claude may do it (L2), per GOVERNANCE.md §2a.

The point: when Claude runs out of its weekly limit, the L1 cards keep moving and the L2 cards wait for the reset. Nobody has to detect the limit. The runner works on its own trigger whether Claude is up or not.

## Lifecycle
1. **Claude writes a card** with `status: ready` and commits it on its working branch (for example `autopilot`). Never on `main`.
2. **Workflow H** (`.github/workflows/l1-runner.yml`) starts on that push. It starts FreeLLMAPI inside the job, and `scripts/l1_runner.py` drafts every `ready` L1 card, runs the card's checks and commits the draft back to the same branch:
   - `drafted`: the draft passed the mechanical checks and waits for Claude.
   - `failed-check`: the model answered but the checks failed; `note` says why.
   - `blocked`: three failed attempts (no model reachable, bad input); `note` says why.
   - On a failed model call the card stays `ready` with `attempts` raised, and the next push retries it.
3. **Claude checks drafts first** on its next run (AUTOPILOT.md rule 1): every `drafted` card's output is verified against the inputs and SOURCES.md, then marked `accepted` (used, and the commit says what L1 drafted and how Claude checked it) or `rejected` (with a `note`, and optionally set back to `ready`).
4. `L2` cards are a to-do list for Claude only. The runner never touches them.

## Card fields
| Field | Meaning |
| --- | --- |
| `id` | lowercase slug, same as the file name without `.json` |
| `layer` | `L1` (free model may draft) or `L2` (Claude only) |
| `status` | see the lifecycle above |
| `for` | what it feeds, e.g. `R4.4 Northern Sonoma chapter captions` |
| `task` | the instruction for the drafter, in plain words |
| `inputs` | repo files the drafter reads (published material only; at most 60,000 characters in all) |
| `output` | where the draft goes, always under `data/drafts/l1/` |
| `format` | `markdown` or `json` |
| `output_schema` | optional repo path of a JSON Schema the JSON draft must pass |
| `max_chars` | optional length cap for the draft |
| `attempts`, `note` | written by the runner |

Example `queue/cards/northern-sonoma-captions.json`:
```json
{
  "id": "northern-sonoma-captions",
  "layer": "L1",
  "status": "ready",
  "for": "R4.4 Northern Sonoma chapter captions",
  "task": "Write one two-sentence caption per chapter, using only facts in the input files. Return JSON {\"captions\": [{\"chapter\": ..., \"text\": ...}]}.",
  "inputs": ["data/regions/northern_sonoma/scenes.json", "SOURCES.md"],
  "output": "data/drafts/l1/northern-sonoma-captions.json",
  "format": "json",
  "max_chars": 4000
}
```

## What the runner refuses
- Inputs outside the repo, hidden files (`.env` and anything starting with a dot), `data/raw/`, owner uploads, keys and certificates. GOVERNANCE.md §2a "Data that never goes to L1" is the rule; the runner enforces the mechanical part of it.
- Anything when the GOVERNANCE.md switch reads `FreeLLMAPI: OFF`, or the repository variables `AGENT_ENABLED` / `FREELLMAPI_ENABLED` are not `true`.
- Running on the default branch.

A drafted file is untrusted material, never a source. It is not used until Claude has checked it.
