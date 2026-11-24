# Data sheet: iSDAsoil v2 soil properties

Soil properties at a point, for the "what to sow" axis (EF-12): acidity,
texture, organic matter and nitrogen.

| Field | Value |
| --- | --- |
| Producer | iSDA (Innovative Solutions for Decision Agriculture) |
| Page | https://www.isda-africa.com/isdasoil/ |
| Licence | CC BY 4.0, "All data are freely available under a Creative Commons Attribution 4.0 International License", checked on the iSDAsoil FAQ on 2026-11-24 |
| Licence obligation | cite iSDA as the source; no citation wording is given on the FAQ |
| Access | REST API `https://api.isda-africa.com`, account required: `POST /login` (form, one-hour token), then `GET /isdasoil/v2/soilproperty?lon=&lat=&depth=&property=` |
| Resolution | 30 m, depths 0-20 cm and 20-50 cm |
| Nature | **predictions** of a machine-learning model trained on about 100,000 soil samples taken across Africa over several decades, with satellite and climate covariates; not laboratory analyses. Each value comes with 50 %, 68 % and 90 % confidence intervals |
| Date of the data | **2021**, publication of the maps (Hengl et al. 2021, *Scientific Reports*), not the date of a sample: this is the `as_of` of every iSDAsoil value. Exact publication day and sampling period: to read in the "Data" section of the article (open access) |
| API use | **personal use only**: a professional account is needed for a service such as an MCP tool (see "Open points") |
| Used here | `ph`, `clay_content` (%), `carbon_organic` (g/kg), `nitrogen_total` (g/kg), with the 90 % interval |
| Code | `src/agritech/data/isdasoil.py`, run by `scripts/ht5_isdasoil.py` |

## Behaviour of the API, as observed on 2026-11-21

- `property` takes **one value per call**: a repeated parameter returns only
  the last property. Three points, two depths and four properties make 24
  calls.
- `ph` has no unit (`unit: null`).
- For some pH values every interval is returned as 0 to 0, which does not
  contain the value. The code treats it as **no uncertainty** and logs it,
  instead of reporting a false interval.
- Each property is a list, even with one element.

## Open points

- **The API account is for personal use.** H-T5 (24 calls, once, for a
  trial) fits it; an MCP tool calling the API for every farmer's question
  does not. Before building the soil tool, either obtain a professional
  account, or read the same maps from the open bulk files (AWS Registry of
  Open Data, CC BY 4.0) once, like CHIRPS, without calling the API.
- `as_of`: the exact publication day of the article is not recorded yet;
  until then only the year 2021 is known, and no day must be invented.
