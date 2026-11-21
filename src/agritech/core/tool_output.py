"""Common output format of every MCP tool (EF-06)."""

from datetime import date
from typing import Annotated, Self

from fastmcp.tools import ToolResult
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


def to_tool_result(result: SourcedValue) -> ToolResult:
    """Wrap a sourced value in the MCP result that Fred's agents read."""
    return ToolResult(
        content=_describe(result),
        structured_content=result.model_dump(mode="json"),
    )


def missing_data(message: str) -> ToolResult:
    """Explicit error when data is missing, never an invented value (ENF-03)."""
    return ToolResult(content=message, is_error=True)


def _describe(result: SourcedValue) -> str:
    # The model reads this text, not the structured data: it must carry the
    # source and the uncertainty so that the agent can cite them (EF-04).
    text = f"{result.value} {result.unit}, source: {result.source.name}"
    if result.source.url:
        text += f" ({result.source.url})"
    text += f", as of {result.as_of.isoformat()}"
    if isinstance(result.uncertainty, Interval):
        low, high = result.uncertainty.low, result.uncertainty.high
        text += f", range {low} to {high} {result.unit}"
    elif result.uncertainty is not None:
        text += f", confidence {result.uncertainty:.0%}"
    return text
