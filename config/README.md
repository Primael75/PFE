# config

Configuration read by every brick, kept out of the code.

## zones/

One profile per zone (EF-01): communes, season onset criterion, crops and
data sources. Adding a zone means adding a file, without changing any
Python code (H-G, CA-02). `tests/config/test_zone_profile.py` checks every
profile: unique communes, complete criterion, ordered ranges, licensed
sources.

| File | Zone | Status |
| --- | --- | --- |
| `zones/zone-a.yaml` | Northern Benin, 27 communes north of 8.7 N | v1, to be reviewed |
