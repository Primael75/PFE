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

Images and generated splits stay outside Git. Other datasets: to be built.
