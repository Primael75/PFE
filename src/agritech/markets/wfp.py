"""WFP food prices for Benin (HDX): which markets cover our crops, and until when.

Domain code for H-T5 (price part). Plain Python, standard library only.
"""

import csv
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

# WFP commodity names per project crop, as found in the Benin file.
# Cowpea (niebe) has no commodity of its own: "Beans (white)" is assumed to be
# white cowpea, to confirm with WFP's market bulletins.
CROP_COMMODITIES: dict[str, tuple[str, ...]] = {
    "maize": ("Maize (white)", "Maize (yellow)", "Maize"),
    "sorghum": ("Sorghum", "Sorghum (red)"),
    "cassava": ("Cassava meal (gari)", "Cassava"),
    "cowpea": ("Beans (white)", "Cowpeas"),
}


@dataclass(frozen=True)
class PriceRow:
    day: date
    department: str
    commune: str
    market: str
    commodity: str
    price_type: str
    unit: str
    price: float


@dataclass(frozen=True)
class MarketCoverage:
    crop: str
    commodity: str
    department: str
    commune: str
    market: str
    first: date
    last: date
    observations: int


def read_prices(path: Path) -> Iterator[PriceRow]:
    """Rows of the WFP CSV. The HDX file has a second line of HXL tags, skipped."""
    with path.open(newline="", encoding="utf-8") as file:
        for record in csv.DictReader(file):
            if record["date"].startswith("#"):
                continue
            yield PriceRow(
                day=date.fromisoformat(record["date"]),
                department=record["admin1"],
                commune=record["admin2"],
                market=record["market"],
                commodity=record["commodity"],
                price_type=record["pricetype"],
                unit=record["unit"],
                price=float(record["price"]),
            )


def coverage(
    rows: Iterable[PriceRow], departments: set[str] | None = None
) -> list[MarketCoverage]:
    """Retail coverage per crop, commodity and market, optionally for some departments."""
    crop_of = {name: crop for crop, names in CROP_COMMODITIES.items() for name in names}
    found: dict[tuple[str, str, str], list[PriceRow]] = {}
    for row in rows:
        crop = crop_of.get(row.commodity)
        if crop is None or row.price_type != "Retail":
            continue
        if departments is not None and row.department not in departments:
            continue
        found.setdefault((crop, row.commodity, row.market), []).append(row)
    result = [
        MarketCoverage(
            crop=crop,
            commodity=commodity,
            department=group[0].department,
            commune=group[0].commune,
            market=market,
            first=min(row.day for row in group),
            last=max(row.day for row in group),
            observations=len(group),
        )
        for (crop, commodity, market), group in found.items()
    ]
    return sorted(result, key=lambda c: (c.crop, c.commodity, c.department, c.market))
