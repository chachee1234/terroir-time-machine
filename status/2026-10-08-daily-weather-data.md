# 2026-10-08 · daily-weather-data

- Added the PRISM daily data the Weather panel (PR #43) reads: `prototype/assets/regions/napa_valley/daily/`, 1 January 1981 to 6 October 2026, 46 yearly files (47 MB), every day present for high, low and rain, 0 failed downloads. Manifest entry `napa_valley-prism-daily` with SHA-256 of each file.
- Sanity: hottest cell 47.9 °C on 6 September 2022 (the September 2022 heat wave); wettest frame-average day 133 mm on 25 October 2021 (the October 2021 atmospheric river).
- Command: `python3 scripts/fetch_prism_daily.py --region data/regions/napa_valley.json` (about 2.5 h from the sandbox; resumable). To add new days later, run it again: cached days are skipped and the years are repacked.
- Next: extend back to 1926 with the coarser Livneh grid (needs owner approval of its host), then fire perimeters by date.
