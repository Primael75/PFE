from datetime import date

import pytest
from pydantic import ValidationError

from agritech.core.tool_output import (
    Interval,
    Source,
    SourcedValue,
    missing_data,
    to_tool_result,
)

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


PRICE = SourcedValue(
    value=250.0,
    unit="XOF/kg",
    source=SOURCE,
    as_of=date(2026, 10, 15),
    uncertainty=Interval(low=240.0, high=280.0),
)


def test_tool_result_carries_the_structured_value():
    result = to_tool_result(PRICE)
    assert result.structured_content == PRICE.model_dump(mode="json")
    assert result.structured_content["as_of"] == "2026-10-15"


def test_tool_result_text_cites_source_date_and_range():
    text = to_tool_result(PRICE).content[0].text
    assert "WFP market prices" in text
    assert "https://example.org/prices" in text
    assert "2026-10-15" in text
    assert "240.0 to 280.0" in text


def test_tool_result_text_shows_confidence():
    diagnosis = SourcedValue(
        value="cassava mosaic disease",
        unit="label",
        source=Source(name="baseline model"),
        as_of=date(2026, 11, 20),
        uncertainty=0.82,
    )
    assert "82%" in to_tool_result(diagnosis).content[0].text


def test_missing_data_is_an_explicit_error():
    result = missing_data("No price for this market in October 2026.")
    assert result.is_error is True
