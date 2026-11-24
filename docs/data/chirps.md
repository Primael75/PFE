# Data sheet: CHIRPS v3 daily rainfall, per commune of zone A

Daily rainfall averaged over each of the 27 communes of zone A
(`config/zones/zone-a.yaml`), input of the season onset calculation
(`src/agritech/sowing/onset.py`).

| Field | Value |
| --- | --- |
| Product | CHIRPS v3 daily, `rnl` product (disaggregated with ERA5), Climate Hazards Center, UCSB |
| Page | https://www.chc.ucsb.edu/data/chirps3 |
| Citation | Climate Hazards Center Infrared Precipitation with Stations version 3 (CHIRPS3) Data Repository, https://doi.org/10.15780/G2JQ0P (2025); Funk et al. (2026), *Scientific Data* 13, 718, https://doi.org/10.1038/s41597-026-07096-4 |
| Licence | CC BY 4.0, with a waiver of copyright by the CHC; checked on the CHIRPS3 page on 2026-11-24 |
| Access | Google Earth Engine, collection `UCSB-CHC/CHIRPS/V3/DAILY_RNL`, one GeoTIFF per year (`scripts/chirps_earth_engine_export.js`) |
| Exported on | 2026-11-21 |
| Grid | 0.05 degree (about 5.5 km), EPSG:4326, 79 x 61 pixels, lon 0.75 to 3.80, lat 8.55 to 12.50 |
| Period | 1981-01-01 to 2025-12-31, 45 yearly files, one band per day named `YYYYMMDD` |
| Commune polygons | geoBoundaries gbOpen BEN ADM2, Public Domain, source Map Maker Ltd. / Stanford Earthworks, boundaries of 2007, release `9469f09`: https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/BEN/ADM2/geoBoundaries-BEN-ADM2.geojson |
| Polygons SHA-256 | `355b4beca2b136ac55633392929886156df65d1fe2f2941cb83efe50c3170371` |
| Files | **outside Git** (GeoTIFFs about 5 MB per year; daily series 17 MB) |

## Method

Script: `scripts/chirps_by_commune.py`, code in `src/agritech/data/chirps.py`.

1. Each commune polygon is rasterised on the CHIRPS grid; a pixel touched by
   the polygon counts for the commune (`all_touched`), so that the smallest
   communes keep enough pixels (Parakou: 27).
2. For each day, the commune value is the mean of its valid pixels.
3. A pixel is **impossible** below 0 mm or above 500 mm: it is counted and
   left out of the mean, so that one bad pixel cannot hide in an average.
4. A day is **missing** when its band is absent from the file or when no
   pixel of the commune is valid. A missing day stays empty, never zero.

## Quality checks, 1981-2025

Run on 2026-11-24 on the 2026-11-21 export.

| Check | Result |
| --- | --- |
| Yearly files | 45 / 45 |
| Missing days, all communes | 0 |
| Impossible values, all pixels | 0 |
| Wettest commune-day | 82.2 mm |

| Commune | Pixels | Mean annual total (mm) | Missing days | Impossible values |
| --- | ---: | ---: | ---: | ---: |
| Banikoara | 181 | 1016 | 0 | 0 |
| Bassila | 217 | 1254 | 0 | 0 |
| Bembereke | 142 | 1145 | 0 | 0 |
| Boukombe | 52 | 1144 | 0 | 0 |
| Copargo | 43 | 1300 | 0 | 0 |
| Djougou | 159 | 1258 | 0 | 0 |
| Gogounou | 208 | 1097 | 0 | 0 |
| Kalale | 153 | 1180 | 0 | 0 |
| Kandi | 147 | 1024 | 0 | 0 |
| Karimama | 253 | 835 | 0 | 0 |
| Kerou | 163 | 1098 | 0 | 0 |
| Kobli | 43 | 1084 | 0 | 0 |
| Kouande | 147 | 1202 | 0 | 0 |
| Malanville | 140 | 985 | 0 | 0 |
| Materi | 84 | 1033 | 0 | 0 |
| N'dali | 153 | 1212 | 0 | 0 |
| Natitingou | 67 | 1220 | 0 | 0 |
| Nikki | 142 | 1160 | 0 | 0 |
| Ouake | 36 | 1333 | 0 | 0 |
| Parakou | 27 | 1212 | 0 | 0 |
| Pehunco | 91 | 1181 | 0 | 0 |
| Perere | 90 | 1170 | 0 | 0 |
| Segbana | 186 | 1082 | 0 | 0 |
| Sinende | 99 | 1168 | 0 | 0 |
| Tanguieta | 234 | 1033 | 0 | 0 |
| Tchaourou | 273 | 1200 | 0 | 0 |
| Toucountouna | 53 | 1202 | 0 | 0 |

The totals rise from the Niger valley (Karimama 835 mm) to the Donga
(Ouake 1,333 mm), the expected north-south gradient.

## Reproduce

1. Run `scripts/chirps_earth_engine_export.js` in the Earth Engine code
   editor and download the 45 GeoTIFFs from Google Drive.
2. Download the polygons from the geoBoundaries link above and check the
   SHA-256.
3. Run, with the communes of `config/zones/zone-a.yaml`:

```bash
uv sync --group rainfall
uv run python scripts/chirps_by_commune.py --tif-dir <GeoTIFFs> \
    --boundaries geoBoundaries-BEN-ADM2.geojson --out <folder> \
    --communes Banikoara Gogounou Kandi Karimama Malanville Segbana \
    Boukombe Kerou Kobli Kouande Materi Natitingou Pehunco Tanguieta \
    Toucountouna Bembereke Kalale "N'dali" Nikki Parakou Perere Sinende \
    Tchaourou Bassila Copargo Djougou Ouake
```
