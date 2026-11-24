# data

## Purpose
Ingestion pipelines: rainfall, soils, commune boundaries, market prices,
crop photos.
Each dataset is checked (no gaps, plausible values) and described in a
sheet (source, date, licence).

## Owner
Each team for its own datasets.

## Provides
Checked datasets in the shared database, to all bricks.

## Status
Photo datasets: `prepare_data.py` builds the leak-free training, validation
and test splits of CCMT, `check_split.py` checks them (see
`docs/data/ccmt.md`). They need the `diagnosis` dependency group:

```bash
uv sync --group diagnosis
uv run python -m agritech.data.prepare_data --root <raw data> --out data_ccmt
uv run python -m agritech.data.check_split --data data_ccmt
```

Rainfall: `chirps.py` averages the CHIRPS v3 daily GeoTIFFs over each
commune and counts missing days and impossible values (see
`docs/data/chirps.md`). It needs the `rainfall` dependency group; run it
with `scripts/chirps_by_commune.py`.

Soils: `isdasoil.py` reads iSDAsoil properties at a point through the API
(see `docs/data/isdasoil.md` and `docs/trials/ht5-soil.md`).

Images, GeoTIFFs and generated files stay outside Git. Other datasets: to
be built.
