# H-T5, price part: WFP prices for zone A

Owner: Messan. Sprint 1 plan, week 2.

**Done when:** list of the markets covered, last date available, data
sheet (source, licence, date), for maize, sorghum, cassava and cowpea.

## How to produce it

```bash
uv run python scripts/ht5_wfp_prices.py --zone-a <departments of zone A>
```

The script downloads the WFP file from HDX into `downloads/` (not
versioned), computes its SHA-256, and writes the data sheet
`docs/data/wfp-prices-benin.md`: source, licence, download date, last
date, and the markets of each crop with their first and last months.

Zone A is not fixed in the project documents yet (zone profile, Aissata).
Until then, run it on the centre and north, the validation zone of the
specification: `Collines Borgou Alibori Atakora Donga`.

## Commodity mapping

| Crop | WFP commodities used |
| --- | --- |
| Maize | `Maize (white)`, `Maize (yellow)` (since 2023-04), `Maize` (old series) |
| Sorghum | `Sorghum`, `Sorghum (red)` |
| Cassava | `Cassava meal (gari)`: gari, not fresh cassava |
| Cowpea | `Beans (white)`, assumed to be white cowpea: to confirm |

Only retail prices are kept (`pricetype = Retail`), in XOF per kg.

## What to expect (not verified by us)

A third-party audit of the same file, downloaded on 2026-10-25
(github.com/codjiabrian44-cpu/benin-agromarket, `docs/DATA.md`), reports:

- 146,501 rows, last date 2026-09-15, monthly retail prices since 2019
  in about 50 markets across the 12 departments;
- a near-total gap in 2017 and 2018;
- licence CC BY-IGO 3.0, as for the other WFP price datasets on HDX.

These figures are only a guide: the data sheet must come from our own
download, with its own checksum.

## Verdict (to fill in after the run)

| Question | Answer |
| --- | --- |
| Zone A markets covered, per crop | |
| Last date available | |
| Markets with data in the last 12 months | |
| H-T5 price part | succeeded / failed |
