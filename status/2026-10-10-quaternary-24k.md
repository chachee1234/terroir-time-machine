# 2026-10-10 · quaternary-24k

Step 2 of the soil research plan: the finer geology under the vineyards.

- **USGS 1:24,000 young deposits in the close-ups.** Witter et al. 2006 (USGS Open-File Report 2006-1037) maps fans, terraces, stream channels and basin deposits by age at 1:24,000. Every Napa Valley close-up it reaches now draws those units over SIM 2956 (1:100,000); hills keep their SIM 2956 bedrock units.
- **Corison:** the winery is on Qhf, Holocene alluvial fan deposits (SIM 2956 only said Qf, fan deposits of any age).
- Suisun Valley gets a geology picture for the first time (outside SIM 2956).
- Hover a unit code in the geology legend for its name. SOURCES.md G43.

New: `scripts/make_quaternary_texture.py`, `scripts/test_quaternary_texture.py`.

To rebuild on a Mac, from the repo folder (the first two lines download the USGS files):

```
curl -o data/raw/of06-1037_4b.shp.zip https://pubs.usgs.gov/of/2006/1037/of06-1037_4b.shp.zip
curl -o data/raw/of06-1037_9.meta.txt https://pubs.usgs.gov/of/2006/1037/of06-1037_9.meta.txt
python3 scripts/make_quaternary_texture.py data/raw/eswn-geol.e00 --zip data/raw/of06-1037_4b.shp.zip --meta data/raw/of06-1037_9.meta.txt
```

Gap: the Corison site card and section still name the SIM 2956 unit (Qf); the 1:24,000 unit shows in the close-up map.
