# H-T1: season onset on hand-built series

Owner: Aissata (team 1, Sowing). Sprint 1 plan.

**Done when:** on rainfall series built by hand, the onset date computed by
the code is exact, and the parameters of the criterion can be changed
without touching the code (CA-02).

## Criterion

Sivakumar (1988), *Agricultural and Forest Meteorology* 42(4), 295-305:
from 1 May, the first day where the rain of 3 consecutive days reaches
20 mm, with no dry spell longer than 7 days in the following 30 days. A day
under 1 mm is dry.

Implementation: `src/agritech/sowing/onset.py`. Every value above is a
field of `OnsetCriterion`, filled from the zone profile.

Choices made where the published rule is not explicit:

| Point | Choice | Why |
| --- | --- | --- |
| Reported day | First day of the 3-day window (`first_day_of_window`, option A, confirmed on 2026-11-24); `threshold_day` is available | Date of the first useful rain, the one the farmer sees; avoids advising a late sowing |
| Check period | 30 days from the first day of the window | Same result on the ten cases as starting after the window |
| Missing day | Adds nothing to a window, counts as dry | Can only delay the onset, never advance it on unobserved rain |
| Negative value | Refused (`ValueError`) | An impossible value is counted and cleaned by the rainfall pipeline, not guessed here |
| End of series | A candidate needs its full 30-day check period | A season is not declared on incomplete data |

## The ten cases

Tests: `tests/sowing/test_onset.py`. Each expected date was counted by hand
on the sliding windows; the count is recalled above each case in the test
file. The series mimic three real seasons of our CHIRPS v3 data:

| Season | Total | Rain days | Longest dry spell |
| --- | --- | --- | --- |
| Kandi 1999 | 1,108 mm | 130 | 7 days |
| Karimama 1983 | 663 mm | 101 | 12 days |
| Ouake 2003 | 1,732 mm | 193 | 3 days |

| Case | What it catches | Expected |
| --- | --- | --- |
| S01 | Reference season; a code reporting the threshold day answers 25 May | 23 May |
| S02 | Window starting the day before the rain, 20.4 mm: rejects `> 20` and rounding | 19 May |
| S03 | Same trap, 20.3 mm | 9 May |
| S04 | False start: three candidates rejected by a 12-day dry spell | 28 May |
| S05 | Dry spell of exactly 7 days: `<= 7`, not `< 7` | 1 May |
| S06 | Dense monsoon, immediate onset | 1 May |
| S07 | Never 20 mm in 3 days: the code must answer "no onset" | none |
| S08 | Two rains 4 days apart are not consecutive | 25 May |
| S09 | 0.5 mm days count as dry | 1 May |
| S10 | Missing day inside the check period | 3 May |

Further tests change one parameter at a time (reported day, tolerated dry
spell, threshold) and check that the date moves as counted by hand, and
that a leap year gives calendar dates.

## Not retained: a second implementation with xclim

A cross-check of the same rule with xarray and xclim was tried. It was not
kept: it added two heavy dependencies, its dry-spell count was rewritten by
hand anyway, so it was not an independent path, and it was a script rather
than a test. It can come back as a test if a reviewer asks for it.

## Verdict

| Question | Answer |
| --- | --- |
| Ten hand-counted dates found by the code | 10 / 10 |
| Parameters changed without touching the code | yes, through `OnsetCriterion` |
| H-T1 | succeeded on hand-built series; real CHIRPS series come with the rainfall pipeline |
