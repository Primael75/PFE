# H-T5, soil part: iSDAsoil at three points of zone A

Owner: Aissata (team 1, Sowing). Sprint 1 plan.

**Done when:** iSDAsoil values are obtained for 3 points of zone A.

## Method

```bash
uv run python scripts/ht5_isdasoil.py --out <folder> \
    --point Kandi 11.279 2.940 --point Djougou 9.696 1.817 \
    --point Karimama 11.912 2.801
```

The account is read from `AGRITECH_ISDASOIL_USERNAME` and
`AGRITECH_ISDASOIL_PASSWORD` (see `.env.example`). The three points span
zone A: Kandi in the centre, Djougou in the wetter south-west, Karimama in
the driest north. Data sheet: `docs/data/isdasoil.md`.

## Results (21 November 2026)

24 values requested, 24 received. Value and 90 % interval; "none" when the
API returned a 0 to 0 interval.

| Point | Depth (cm) | pH | Clay (%) | Organic carbon (g/kg) | Total nitrogen (g/kg) |
| --- | --- | --- | --- | --- | --- |
| Kandi | 0-20 | 6.1 (5.9-6.3) | 16 (9.4-22.6) | 5.0 (4.1-6.1) | 0.5 (0.4-0.7) |
| Kandi | 20-50 | 6.2 (none) | 22 (15.4-28.6) | 2.7 (2.1-3.3) | 0.3 (0.2-0.5) |
| Djougou | 0-20 | 5.9 (5.7-6.1) | 18 (16.4-19.6) | 6.4 (5.3-7.7) | 0.7 (0.6-0.9) |
| Djougou | 20-50 | 5.8 (5.6-6.0) | 24 (20.7-27.3) | 3.5 (2.8-4.3) | 0.5 (0.3-0.7) |
| Karimama | 0-20 | 6.3 (none) | 20 (10.1-29.9) | 7.2 (5.9-8.6) | 0.9 (0.7-1.1) |
| Karimama | 20-50 | 6.2 (none) | 27 (15.5-38.5) | 4.0 (3.2-4.8) | 0.6 (0.5-0.7) |

The values were fetched with an earlier script of the same calls; the
parsing in `src/agritech/data/isdasoil.py` is tested on the same response
format (`tests/data/test_isdasoil.py`).

## Verdict

| Question | Answer |
| --- | --- |
| Values for 3 points of zone A | yes, 24 / 24, both depths |
| Uncertainty available | yes, except 3 of the 6 pH values (0 to 0 intervals) |
| H-T5 soil part | succeeded |
| Date of the values | 2021, publication of the maps; exact day to read in the article |
| Open | the API account is for personal use: a professional account, or the open bulk files, is needed for an MCP tool |
