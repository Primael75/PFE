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

## Verdict (2026-11-22)

File downloaded on 2026-11-22, SHA-256 `a6d1d42a0778468b3fdb8ed8dd0ba9f3e038962b38da0d0db44830d34878795b`,
148,380 rows. Licence checked on the HDX page: CC BY-IGO.

| Question | Answer |
| --- | --- |
| Zone A markets covered, per crop | 22 for each of the four crops, in the five departments (Alibori 3, Atakora 5, Borgou 7, Collines 4, Donga 3) |
| Last date available | 2026-10-15 |
| Markets with data in the last 12 months | 21 for each crop; N'Dali (Borgou) stopped in 2016-02 |
| H-T5 price part | **Succeeded** |

Reservations:

- Zone A is provisional (centre and north) until the zone profile fixes it.
- Cassava is priced as gari, not fresh cassava.
- Cowpea is assumed to be `Beans (white)`: to confirm in a WFP bulletin.
- A gap in 2017 and 2018 is reported by a third-party audit: to check before
  using the series for forecasting.

Reservations:

- Zone A is provisional (centre and north) until the zone profile fixes it.
- Cassava is priced as gari, not fresh cassava.
- Cowpea is assumed to be `Beans (white)`: to confirm in a WFP bulletin.
- A gap in 2017 and 2018 is reported by a third-party audit: to check before
  using the series for forecasting.
