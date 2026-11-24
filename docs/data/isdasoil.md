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
| Nature | **predictions** of a machine-learning model, not laboratory analyses; each value comes with 50 %, 68 % and 90 % confidence intervals |
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

- The API terms of use (https://www.isda-africa.com/terms-of-use) have not
  been read yet: check that they allow our use before an MCP tool calls the
  API.
- The date of the predictions (needed as `as_of` in `SourcedValue`) is not
  given by the API: to find in the iSDAsoil documentation.
