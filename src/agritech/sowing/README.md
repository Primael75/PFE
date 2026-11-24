# sowing

## Purpose
When to sow: season onset, sowing window and false-start risk per commune.
What to sow: suitability score for maize, sorghum, cassava and cowpea.

## Owner
Team 1 (Sowing).

## Provides
Commune maps and season onset dates, to team 3.

## Status
- `onset.py`: season onset date of a daily rainfall series, with the
  Sivakumar (1988) criterion family. Every parameter is a field of
  `OnsetCriterion`, read from the zone profile. Domain code, no I/O.
  Checked on ten hand-built series (H-T1), see `docs/trials/ht1-onset.md`.
- MCP tools, sowing window and false-start risk: sprint 2.
