# 2026-10-08 · daily-weather

- Added a Weather panel to the Napa–Sonoma viewer: pick any day from 1 January 1981 to recent days and see PRISM 4 km daily high, low or rain coloured on the terrain, frame extremes, and growing degree days at Corison since 1 April. Owner approved PRISM daily data 2026-10-08 (AUTOPILOT.md, SOURCES G41).
- Data: `python3 scripts/fetch_prism_daily.py --region data/regions/napa_valley.json` (about 50,000 daily files, resumable; repack only with `--pack`). Output in `prototype/assets/regions/napa_valley/daily/`.
- Check: `python3 -m unittest discover -s scripts -p 'test_*.py'`; headless Chromium opened `timemachine.html?t=0`, turned Weather on, switched days and layers, no console errors besides the repo-root files missing when serving `prototype/` alone.
- Next: extend back to 1926 with the coarser Livneh grid (needs owner approval of the NOAA PSL host), then fire perimeters by date.
