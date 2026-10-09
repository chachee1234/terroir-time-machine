# Tests and CI gates

Every pull request runs `.github/workflows/ci.yml`. All four gates must be green to merge.

| Gate | What it checks | Run it yourself |
|---|---|---|
| Unit | Content validation (`scripts/validate.py`) and the Python unit tests in `scripts/test_*.py` | `pip install -r requirements.txt -r requirements-dev.txt`, `python3 scripts/validate.py`, then `python3 -m unittest discover -s scripts -p 'test_*.py'` |
| Lint | Python compiles and passes pyflakes; every inline `<script>` in `prototype/` and every `.mjs` parses | `python3 -m compileall -q scripts` and `node tests/lint_js.mjs` |
| Security | No secrets in tracked files; workflows have least-privilege tokens, SHA-pinned actions and no untrusted `${{ }}` in scripts; pages load scripts only from the allowed CDNs with integrity hashes; no risky Python patterns (network access only through `scripts/net.py`, which refuses non-http(s) URLs); Bandit; pip-audit | `python3 scripts/security_check.py` (add `--online` to check the CDN hashes) |
| Browser | Chromium headless, `node --test`. **Functional**: every page loads with no errors, missing files or requests to unlisted hosts; timeline, play, keyboard, deep links, mobile layout, reduced motion, no-WebGL message (ACCEPTANCE_TESTS U01-U05). **Integration**: `build_share.py` output runs from a bare `file://` path with the feedback panel working. **Security**: script-injection and junk values in every URL parameter a page reads | see below |

## Browser tests on your Mac

The tests never touch the network. three.js r128 comes from a local copy:

```
git clone --depth 1 --branch r128 --filter=blob:none --sparse https://github.com/mrdoob/three.js ../three-r128
git -C ../three-r128 sparse-checkout set --no-cone /build/three.min.js /examples/js/controls/OrbitControls.js
npm install --no-save --no-package-lock playwright@1.56.1
npx playwright install chromium
node --test "tests/browser/*.test.mjs"
```

The default location for the copy is `../three-r128` next to the repo; set `THREE_DIR` to use another.

## Rules

- Never skip, disable or loosen a test to get a gate green. Fix the code, or fix the test only when the test itself is wrong, and say why in the PR.
- `OPTIONAL` in `tests/browser/harness.mjs` and `PENDING_DATA` in `scripts/test_build_share.py` list files the viewer asks for whose data arrives in a later PR. Remove the entry when the data lands.
- Updating three.js means updating the `integrity` hashes in `prototype/timemachine.html`, `prototype/gibraltar.html` and `THREE_TAG` in `scripts/build_share.py`; the security gate fetches the CDN files and fails on a mismatch.
