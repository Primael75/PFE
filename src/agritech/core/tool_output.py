"""Common output format of every MCP tool (EF-06)."""

from datetime import date
from typing import Annotated, Self

from pydantic import BaseModel, Field, model_validator

# A confidence level between 0 and 1, used for example by the diagnosis.
Probability = Annotated[float, Field(ge=0, le=1)]


class Interval(BaseModel):
    """Range of plausible values, in the same unit as the value."""

    low: float
    high: float

    @model_validator(mode="after")
    def check_bounds(self) -> Self:
        if self.low > self.high:
            raise ValueError("low must not be greater than high")
        return self


class Source(BaseModel):
    """Where a value comes from. Web sources carry their URL (EF-05)."""

    name: str
    url: str | None = None


class SourcedValue(BaseModel):
    """Business content of every MCP tool result, so that no figure is unsourced (EF-04)."""

    value: float | str
    unit: str
    source: Source
    as_of: date  # date of the data, not of the computation
    uncertainty: Interval | Probability | None = None
