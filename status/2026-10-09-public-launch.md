## Public launch prep: licence, README, GitHub Pages deploy (2026-10-09)

Branch `public-launch`. Owner request: make the repository publicly shareable. Not merged.

**What changed**
- `LICENSE` (MIT, copyright 2026 chachee1234) and `LICENSE-CONTENT.md` (chapter text and docs CC BY 4.0; datasets keep their own licences, see SOURCES.md).
- `README.md` for non-experts, with screenshots in `docs/img/` (headless Chromium: Today chapter, 250 Ma globe).
- `.github/workflows/pages.yml`: push to main and manual run; `scripts/build_site.py` builds `_site/` (prototype/ plus the root files the pages fetch with `../` paths, found by scanning the pages: SCENES.json, data/plates/stylized.json, data/regions/; plus index.html and the licence files). Excludes data/raw, .venv, notebooks, tests, USGS, caches. Fails over 900 MB and prints the size. Actions pinned to SHAs (configure-pages v6.0.0, upload-pages-artifact v5.0.0, deploy-pages v5.0.1, checkout v7.0.1); top-level `permissions: {}`, build job `contents: read`, deploy job `pages: write` + `id-token: write`. Not gated on AGENT_ENABLED.
- Root `index.html` redirects to `prototype/timemachine.html`.
- Weather: the viewer asks for `daily/index.json` only when `prototype/assets/regions/index.json` lists the `daily` layer for napa_valley, so a site without the data shows no Weather chip and no 404. `fetch_prism_daily.py` adds the layer when it packs; `test_prism_daily` fails if layer and files disagree. `PENDING_DATA` in test_build_share became `OPTIONAL_DATA`; `OPTIONAL` in the browser harness is now empty (any 404 fails).
- Social preview: description, Open Graph and Twitter card tags on timemachine.html (and index.html); image `prototype/assets/social-card.jpg` (1200 × 630, left out of the share build).
- Untracked two stray `.pyc` files (`scripts/__pycache__`), already covered by .gitignore.

**Commands and results**
- `python3 scripts/validate.py`: PASS. `python3 -m unittest discover -s scripts -p 'test_*.py'`: 175 tests OK (3 skipped, as on main).
- `node tests/lint_js.mjs`: PASS. `python3 scripts/security_check.py`: all ok. pyflakes not run locally (pip index blocked in the sandbox); CI runs it.
- `python3 scripts/build_site.py --out /tmp/_site`: 298 files, 108.2 MB.
- Served `/tmp/_site`, opened 18 pages in headless Chromium (every region, regions view, 250 Ma, gibraltar, sources, three films, globe redirect, feedback, root redirect): no console errors, no missing files (Google Fonts are blocked in the sandbox and were ignored). Same again with PR #45's daily files added: Weather chip appears, no errors.
- Browser test suite: see the PR.

**Safety scan (whole history, 126 commits, all branches)**: no secrets, tokens, keys or .env files. Findings reported to the owner in the PR; no history rewritten.

**Next smallest action**: owner merges, then turns on Pages (Settings → Pages → Source: GitHub Actions). PR #45 must add `"daily"` to napa_valley's layers when it is updated from main (re-run `fetch_prism_daily.py --pack` or add it by hand).
