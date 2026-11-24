# Sprint 1 delivery: Aicha

| | |
| --- | --- |
| Team | 1, Sowing |
| Role | When and what to sow: rainfall, soils, zone profile, season onset |
| Date | 25 November 2026 |
| Scope | Zone A, the 27 communes of northern Benin (single rainy season); maize, sorghum, cowpea, cassava |
| Pull requests | #21 `feat/chirps-isdasoil` (rainfall and soils): https://github.com/Primael75/PFE/pull/21; #22 `feat/zone-profile` (zone A profile): https://github.com/Primael75/PFE/pull/22; #23 `feat/onset-reference-cases` (H-T1): https://github.com/Primael75/PFE/pull/23 |

## Summary

| Task | Status | Main result | Evidence |
| --- | --- | --- | --- |
| Zone A profile (communes, criterion, crops, sources) | Done, to be reviewed by Messan | 27 communes north of 8.7 N, Sivakumar (1988) criterion, 4 crops, 3 sources with their licences | `config/zones/zone-a.yaml`, #22 |
| CHIRPS rainfall per commune | Done | 45 years (1981-2025), 27 communes, 0 missing days, 0 impossible values | `docs/data/chirps.md`, #21 |
| H-T1: onset date exact on hand-built series | Succeeded | 10 of 10 hand-counted dates found; parameters changed without touching the code | `docs/trials/ht1-onset.md`, #23 |
| H-T5, soil part: iSDAsoil for 3 points | Succeeded | 24 of 24 values, 2 depths, with their 90 % interval | `docs/trials/ht5-soil.md`, #21 |
| Data sheets (source, date, licence) | Done | CHIRPS v3 CC BY 4.0; iSDAsoil CC BY 4.0; geoBoundaries Public Domain | `docs/data/chirps.md`, `docs/data/isdasoil.md` |

## 1. Zone A profile

File: `config/zones/zone-a.yaml`, read by every brick. The code holds no place parameter: adding a zone means adding a file (H-G, CA-02).

- **Extent rule:** a commune belongs to zone A when its centroid lies north of 8.7 N. South of this line Benin has two rainy seasons, which a single search window cannot handle.
- **Result:** exactly 27 communes, the four departments Alibori (6), Atakora (9), Borgou (8) and Donga (4). Names are spelled as in geoBoundaries, the key used to join rainfall to communes.
- **Corrections during the sprint:** the first draft listed three communes twice (Kalale, Banikoara, Gogounou), missed three (Segbana, Kobli, Parakou), and used accented names that matched no polygon. A test now checks every profile (unique communes, complete criterion, ordered ranges, licensed sources).
- **Crops:** maize, sorghum, cowpea, cassava, with FAO water needs, cycle length, rooting depth and optimal pH.

| Crop | Water need (mm) | Cycle (days) | Optimal pH | Source |
| --- | --- | ---: | --- | --- |
| Maize | 500-800 | 120 | 5.5-7.5 | FAO Land & Water |
| Sorghum | 450-650 | 130 | 5.5-8.0 | FAO Land & Water |
| Cowpea | 300-500 | 90 | 5.5-7.5 | FAO Paper 33, "Bean" values |
| Cassava | 400-750 | 300 | 5.0-7.0 | FAO, Save and Grow: Cassava |

## 2. Rainfall: CHIRPS v3 per commune

Details: `docs/data/chirps.md`. Code: `src/agritech/data/chirps.py`, run by `scripts/chirps_by_commune.py`.

- **Source:** CHIRPS v3 daily, `rnl` product (Climate Hazards Center, UCSB), 0.05 degree grid. Licence CC BY 4.0, checked on the CHC page on 24 November 2026.
- **Access:** Google Earth Engine, one GeoTIFF per year (`scripts/chirps_earth_engine_export.js`). A single 1981-2025 export would stack about 16,400 bands and fail. The `rnl` product is used because `sat` only starts in 1998.
- **Commune polygons:** geoBoundaries gbOpen BEN ADM2, Public Domain, SHA-256 recorded.

Rules chosen:

1. A pixel touched by the commune polygon counts for it, so that the smallest communes keep enough pixels (Parakou: 27).
2. The commune value of a day is the mean of its valid pixels.
3. A pixel below 0 mm or above 500 mm is **impossible**: it is counted and left out of the mean, so that one bad pixel cannot hide in an average.
4. A day is **missing** when its band is absent from the file or when no pixel of the commune is valid. A missing day stays empty, never zero.

Results on 1981-2025: 45 of 45 yearly files, **0 missing days, 0 impossible values**, wettest commune-day 82.2 mm. Mean annual totals rise from the Niger valley (Karimama, 835 mm) to the Donga (Ouake, 1,333 mm), the expected north-south gradient. Per-commune table in the data sheet.

## 3. H-T1: season onset

Details: `docs/trials/ht1-onset.md`. Code: `src/agritech/sowing/onset.py`. Tests: `tests/sowing/test_onset.py`.

**Criterion, Sivakumar (1988):** from 1 May, the first day where 3 consecutive days total at least 20 mm, with no dry spell longer than 7 days in the next 30 days; a day under 1 mm is dry. Every value is a field of `OnsetCriterion`, filled from the zone profile.

Rules chosen where the published rule is not explicit:

| Point | Rule | Why |
| --- | --- | --- |
| Reported day | First day of the 3-day window (option A, confirmed on 24 November) | The first useful rain, the one the farmer sees; avoids advising a late sowing |
| Missing day | Adds nothing to a window and counts as dry | Can only delay the onset, never advance it on unobserved rain |
| Negative value | Refused with an error | Impossible values are cleaned by the rainfall pipeline, not guessed here |
| End of series | A candidate needs its full 30-day check period | No season declared on incomplete data |

**Ten hand-built series**, modelled on three real CHIRPS seasons: Kandi 1999 (1,108 mm, rain every other day), Karimama 1983 (663 mm, a 12-day dry spell), Ouake 2003 (1,732 mm, rain almost every day). Each expected date was counted by hand on the sliding windows and is never computed by the code under test. The traps covered: a threshold passed by 0.3 or 0.4 mm, a window starting the day before the rain, a false start, a dry spell of exactly 7 days, a season that never starts, non-consecutive rains, negligible rains, a missing day.

Further tests change one parameter at a time (reported day, tolerated dry spell, threshold) and check a leap year. **Verdict: succeeded**, 10 of 10.

## 4. H-T5, soil part: iSDAsoil

Details: `docs/trials/ht5-soil.md` and `docs/data/isdasoil.md`. Code: `src/agritech/data/isdasoil.py`, run by `scripts/ht5_isdasoil.py`.

- Three points spanning zone A: Kandi (centre), Djougou (wetter south-west), Karimama (driest north); depths 0-20 and 20-50 cm; pH, clay, organic carbon, total nitrogen.
- **24 of 24 values received**, each with its 90 % interval, the widest the API gives.
- The API keeps only the last of a repeated `property` parameter: one call per property.
- For 3 of the 6 pH values the API returns a 0 to 0 interval, which does not contain the value. It is reported as **no uncertainty**, not as a false interval.
- iSDAsoil values are model predictions (about 100,000 soil samples across Africa, with satellite and climate covariates), not laboratory analyses. Their date (`as_of`) is the publication of the maps, 2021, not the date of a sample.
- **Verdict: succeeded.**

## 5. Decisions

- **Zone profile in `config/zones/`**, a new top-level directory agreed before creation: the profile is read by every brick, not by one.
- **Onset day: option A**, the first day of the window; `threshold_day` stays available in the profile.
- **rasterio for the GeoTIFFs**, in a separate `rainfall` dependency group installed by CI; geopandas dropped, the GeoJSON is read with the standard library.
- **No xclim cross-check:** two heavy dependencies, a dry-spell count rewritten by hand anyway, so not an independent path. Can come back as a test if a reviewer asks for it.
- **Credentials** for iSDAsoil come from `AGRITECH_ISDASOIL_USERNAME` and `AGRITECH_ISDASOIL_PASSWORD`, never from the code.

## 6. Limits

- **rasterio licence:** its wheels bundle native libraries loaded dynamically, some under LGPL (GEOS, libiconv) or an MPL/GPL/LGPL tri-licence (spatialite, freexl). To settle in ADR-0005; fallback tifffile and imagecodecs (BSD-3), checked to read identical values.
- **iSDAsoil API account is for personal use.** Fine for the H-T5 trial; an MCP tool needs a professional account, or the open bulk maps read once like CHIRPS.
- **`as_of` of iSDAsoil:** only the year 2021 is recorded; the exact publication day and the sampling period are to read in the article.
- **Cowpea:** FAO gives no own values; the "Bean" values are an approximation.
- **Extent rule:** Bassila and Tchaourou extend south of 8.7 N; they are kept because their centroid is north of it.
- **Border pixels** are counted for both neighbouring communes (`all_touched`).
- **Onset on real series not run yet:** H-T1 is checked on hand-built series only.
- **Zone A for prices:** `docs/trials/ht5-prices.md` still uses the provisional zone with Collines (4 markets), which is not in zone A.

## 7. Next (sprint 2)

1. Run the onset on the 45 years of CHIRPS for the 27 communes and check the dates against the expected regional calendar.
2. Sowing window and false-start risk from the onset series.
3. First Sowing MCP tool from `onset.py`, returning a `SourcedValue`.
4. Suitability score per crop from the crop needs of the profile and the soil values.
5. iSDAsoil: professional account or open bulk maps; exact publication date.
6. A loader for the zone profile, so that bricks read it instead of repeating the communes.

## Cross-validation

| Reviewer | Verdict | Date |
| --- | --- | --- |
| | | |
