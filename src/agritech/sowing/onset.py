"""Rainy season onset: the first day from which sowing is not a false start.

Domain code, no I/O. Every threshold comes from an `OnsetCriterion`, read
from the zone profile: another zone or another published rule changes the
profile, not this code (H-T1, CA-02).
"""

import math
from collections.abc import Sequence
from datetime import date, timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, PositiveInt


class OnsetDay(StrEnum):
    """Which day of the wet window is reported as the onset."""

    # First day of the window: the first useful rain, the farmer's date.
    FIRST_DAY_OF_WINDOW = "first_day_of_window"
    # Last day of the window, when the cumulative rain reaches the threshold.
    THRESHOLD_DAY = "threshold_day"


class MonthDay(BaseModel):
    model_config = ConfigDict(frozen=True)

    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)

    def in_year(self, year: int) -> date:
        return date(year, self.month, self.day)


class OnsetCriterion(BaseModel):
    """Onset rule of the Sivakumar (1988) family, with all its parameters.

    A day starts the season when the rain of `window_days` consecutive days
    reaches `window_threshold_mm`, and no dry spell longer than
    `max_dry_spell_days` occurs in the `check_days` days starting that day.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    reference: str
    search_from: MonthDay
    search_to: MonthDay
    window_days: PositiveInt
    window_threshold_mm: NonNegativeFloat
    check_days: PositiveInt
    max_dry_spell_days: int = Field(ge=0)
    wet_day_mm: NonNegativeFloat
    onset_day: OnsetDay


def season_onset(
    rain_mm: Sequence[float | None], first_day: date, criterion: OnsetCriterion
) -> date | None:
    """Onset date in the year of `first_day`, or None when no day qualifies.

    `rain_mm` holds one daily value per day from `first_day`. A missing day
    (None or NaN) adds nothing to a window and counts as dry: both choices
    can only delay the onset, never advance it on rain that was not observed.
    A negative value is impossible and must be cleaned upstream.
    """
    _check_values(rain_mm)
    year = first_day.year
    start = (criterion.search_from.in_year(year) - first_day).days
    end = (criterion.search_to.in_year(year) - first_day).days
    if start < 0:
        raise ValueError(
            f"series starts on {first_day}, after the search start "
            f"{criterion.search_from.in_year(year)}"
        )

    for k in range(start, end + 1):
        # A candidate is only judged on a complete check period.
        if k + max(criterion.window_days, criterion.check_days) > len(rain_mm):
            return None
        window = rain_mm[k : k + criterion.window_days]
        if sum(_rain(v) for v in window) < criterion.window_threshold_mm:
            continue
        check = rain_mm[k : k + criterion.check_days]
        if (
            _longest_dry_spell(check, criterion.wet_day_mm)
            > criterion.max_dry_spell_days
        ):
            continue
        if criterion.onset_day is OnsetDay.THRESHOLD_DAY:
            k += criterion.window_days - 1
        return first_day + timedelta(days=k)
    return None


def _check_values(rain_mm: Sequence[float | None]) -> None:
    for i, value in enumerate(rain_mm):
        if value is not None and value < 0:
            raise ValueError(f"impossible rain value {value} mm at index {i}")


def _rain(value: float | None) -> float:
    return 0.0 if value is None or math.isnan(value) else value


def _longest_dry_spell(rain_mm: Sequence[float | None], wet_day_mm: float) -> int:
    longest = current = 0
    for value in rain_mm:
        current = current + 1 if _rain(value) < wet_day_mm else 0
        longest = max(longest, current)
    return longest
