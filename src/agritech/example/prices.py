"""Example domain logic for the MCP server template.

The data is fictitious: it only shows how a tool looks up a value and
reports missing data. Replace it with your brick's real data source.
"""

from datetime import date

from agritech.core.tool_output import Source, SourcedValue

_SOURCE = Source(name="Template demo data (fictitious)")
_AS_OF = date(2026, 10, 15)

# (market, crop) -> price in XOF/kg. Fictitious values and market names.
_PRICES: dict[tuple[str, str], float] = {
    ("Market A", "maize"): 250.0,
    ("Market B", "maize"): 210.0,
}


def get_demo_price(market: str, crop: str) -> SourcedValue | None:
    """Return the demo price of a crop on a market, or None if it is unknown."""
    price = _PRICES.get((market, crop))
    if price is None:
        return None
    return SourcedValue(value=price, unit="XOF/kg", source=_SOURCE, as_of=_AS_OF)
