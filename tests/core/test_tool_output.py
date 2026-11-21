from datetime import date

import pytest
from pydantic import ValidationError

from agritech.core.tool_output import Interval, Source, SourcedValue

SOURCE = Source(name="WFP market prices", url="https://example.org/prices")


def test_numeric_value_with_interval():
    result = SourcedValue(
        value=250.0,
        unit="XOF/kg",
        source=SOURCE,
        as_of=date(2026, 10, 15),
        uncertainty=Interval(low=240.0, high=280.0),
    )
    assert result.uncertainty == Interval(low=240.0, high=280.0)


def test_text_value_with_probability():
    result = SourcedValue(
        value="cassava mosaic disease",
        unit="label",
        source=Source(name="baseline model"),
        as_of=date(2026, 11, 20),
        uncertainty=0.82,
    )
    assert result.uncertainty == 0.82


def test_uncertainty_is_optional():
    result = SourcedValue(
        value=250.0, unit="XOF/kg", source=SOURCE, as_of=date(2026, 10, 15)
    )
    assert result.uncertainty is None


def test_probability_above_one_is_rejected():
    with pytest.raises(ValidationError):
        SourcedValue(
            value="cassava mosaic disease",
            unit="label",
            source=SOURCE,
            as_of=date(2026, 11, 20),
            uncertainty=1.4,
        )


def test_interval_with_inverted_bounds_is_rejected():
    with pytest.raises(ValidationError):
        Interval(low=300.0, high=200.0)


def test_missing_source_is_rejected():
    with pytest.raises(ValidationError):
        SourcedValue(value=250.0, unit="XOF/kg", as_of=date(2026, 10, 15))
