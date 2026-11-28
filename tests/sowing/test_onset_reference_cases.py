"""H-T1: ten hand-built rainfall series whose onset date is known.

Each expected date was counted by hand on the sliding windows, as recalled
above each case; it is never computed by the code under test. The series
mimic three real CHIRPS seasons of northern Benin: Kandi 1999 (rain every
other day), Karimama 1983 (sparse, 12-day dry spell), Ouake 2003 (rain
almost every day). See docs/trials/ht1-onset.md.
"""

from datetime import date

import pytest

from agritech.sowing.onset import OnsetCriterion, OnsetDay, season_onset

YEAR = 2001  # not a leap year: day indexes match the hand counts
FIRST_DAY = date(YEAR, 1, 1)

# Sivakumar (1988), as written in the zone A profile.
SIVAKUMAR = OnsetCriterion(
    name="sivakumar_1988",
    reference="Sivakumar (1988), Agricultural and Forest Meteorology 42(4)",
    search_from={"month": 5, "day": 1},
    search_to={"month": 9, "day": 30},
    window_days=3,
    window_threshold_mm=20,
    check_days=30,
    max_dry_spell_days=7,
    wet_day_mm=1.0,
    onset_day=OnsetDay.FIRST_DAY_OF_WINDOW,
)


def d(day: int, month: int) -> date:
    return date(YEAR, month, day)


def series(rains: list[tuple[date, float | None]]) -> list[float | None]:
    values: list[float | None] = [0.0] * 365
    for day, mm in rains:
        values[(day - FIRST_DAY).days] = mm
    return values


def every(start: date, step: int, count: int, mm: float) -> list[tuple[date, float]]:
    return [(date.fromordinal(start.toordinal() + step * i), mm) for i in range(count)]


CASES = {
    # 23-25 May = 17 + 0 + 17 = 34 mm, no dry spell. The threshold day is 25 May.
    "S01 reference season, Kandi 1999 rhythm": (
        every(d(23, 5), 2, 100, 17.0),
        d(23, 5),
    ),
    # 19-21 May = 0 + 14.0 + 6.4 = 20.4 mm: the window starts the day before the rain.
    "S02 threshold passed by 0.4 mm, Karimama 1983": (
        [(d(20, 5), 14.0), (d(21, 5), 6.4)] + every(d(25, 5), 2, 90, 15.0),
        d(19, 5),
    ),
    # 9-11 May = 0 + 13.0 + 7.3 = 20.3 mm, the thinnest margin of the set.
    "S03 threshold passed by 0.3 mm, Ouake 2003": (
        [(d(10, 5), 13.0), (d(11, 5), 7.3)] + every(d(14, 5), 1, 90, 12.0),
        d(9, 5),
    ),
    # Windows of 13, 14 and 15 May reach 25 mm but 16-27 May is 12 dry days > 7.
    "S04 false start, 12 dry days": (
        [(d(15, 5), 25.0)] + every(d(28, 5), 2, 50, 18.0),
        d(28, 5),
    ),
    # 1-3 May = 35 mm; 3-9 May is 7 dry days, the tolerated maximum.
    "S05 dry spell exactly at the limit": (
        [(d(1, 5), 25.0), (d(2, 5), 10.0)] + every(d(10, 5), 2, 90, 15.0),
        d(1, 5),
    ),
    # 1-3 May = 36 mm: the search starts on 1 May, the onset is immediate.
    "S06 dense monsoon, Ouake 2003": (
        every(d(1, 5), 1, 150, 12.0),
        d(1, 5),
    ),
    # One 7 mm rain per 3-day window: never 20 mm.
    "S07 poor season, no onset": (
        every(d(1, 5), 3, 60, 7.0),
        None,
    ),
    # 3 May and 7 May are never in the same 3-day window; 25-27 May = 36 mm.
    "S08 two separate rains are not enough": (
        [(d(3, 5), 10.0), (d(7, 5), 10.0)] + every(d(25, 5), 2, 50, 18.0),
        d(25, 5),
    ),
    # 0.5 mm days are dry (wet day: 1 mm); 3-8 May is 6 dry days.
    "S09 negligible rains count as dry": (
        [(d(1, 5), 25.0), (d(2, 5), 10.0)]
        + every(d(4, 5), 1, 5, 0.5)
        + every(d(9, 5), 2, 90, 15.0),
        d(1, 5),
    ),
    # 3-5 May = 0 + 0 + 25 = 25 mm; the missing 6 May counts as dry, spell of 2.
    "S10 missing day": (
        [(d(5, 5), 25.0), (d(6, 5), None), (d(7, 5), 10.0)]
        + every(d(8, 5), 2, 90, 15.0),
        d(3, 5),
    ),
}


@pytest.mark.parametrize("rains, expected", CASES.values(), ids=CASES.keys())
def test_onset_matches_the_hand_count(rains, expected):
    assert season_onset(series(rains), FIRST_DAY, SIVAKUMAR) == expected


def test_ten_reference_cases():
    assert len(CASES) == 10


def test_threshold_day_variant_reports_the_last_day_of_the_window():
    rains, _ = CASES["S01 reference season, Kandi 1999 rhythm"]
    criterion = SIVAKUMAR.model_copy(update={"onset_day": OnsetDay.THRESHOLD_DAY})
    assert season_onset(series(rains), FIRST_DAY, criterion) == d(25, 5)


def test_a_longer_tolerated_dry_spell_accepts_the_false_start():
    # Same series as S04: with 12 dry days tolerated, 13 May is accepted.
    rains, _ = CASES["S04 false start, 12 dry days"]
    criterion = SIVAKUMAR.model_copy(update={"max_dry_spell_days": 12})
    assert season_onset(series(rains), FIRST_DAY, criterion) == d(13, 5)


def test_a_higher_threshold_moves_the_onset():
    # Same series as S02: 20.4 mm no longer passes 25 mm; 25-27 May = 30 mm.
    rains, _ = CASES["S02 threshold passed by 0.4 mm, Karimama 1983"]
    criterion = SIVAKUMAR.model_copy(update={"window_threshold_mm": 25})
    assert season_onset(series(rains), FIRST_DAY, criterion) == d(25, 5)


def test_dates_follow_the_calendar_in_a_leap_year():
    first_day = date(2004, 1, 1)
    rain = [0.0] * 366
    for i in range(121, 366, 2):  # from 1 May 2004, index 121 in a leap year
        rain[i] = 17.0
    assert season_onset(rain, first_day, SIVAKUMAR) == date(2004, 5, 1)


def test_negative_rain_is_rejected():
    rain = series([(d(1, 5), 25.0), (d(2, 5), -5.0)])
    with pytest.raises(ValueError, match="impossible"):
        season_onset(rain, FIRST_DAY, SIVAKUMAR)


def test_series_starting_after_the_search_start_is_rejected():
    with pytest.raises(ValueError, match="search start"):
        season_onset([0.0] * 200, d(1, 6), SIVAKUMAR)


def test_candidate_without_a_full_check_period_is_not_judged():
    # Rain on 1-3 May but the series stops on 20 May: the 30-day check is incomplete.
    rain = series([(d(1, 5), 25.0)])[: (d(21, 5) - FIRST_DAY).days]
    assert season_onset(rain, FIRST_DAY, SIVAKUMAR) is None
