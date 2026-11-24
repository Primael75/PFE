"""CHIRPS v3 daily rainfall averaged per commune, with its quality counts.

Reads the yearly GeoTIFFs exported from Earth Engine (one band per day,
described YYYYMMDD) and the commune polygons of geoBoundaries. Needs the
`rainfall` dependency group. See docs/data/chirps.md.
"""

import calendar
import json
import logging
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import Affine

logger = logging.getLogger(__name__)

# A daily value above this is treated as an error, not as rain: it is far
# above the wettest commune-day of 1981-2025 over zone A (docs/data/chirps.md).
MAX_PLAUSIBLE_MM = 500.0


@dataclass(frozen=True)
class CommuneDay:
    commune: str
    day: date
    rain_mm: float | None  # None when no valid pixel: missing, never zero
    valid_pixels: int


@dataclass(frozen=True)
class YearQuality:
    commune: str
    year: int
    pixels: int
    expected_days: int
    missing_days: int  # absent from the file, or without any valid pixel
    impossible_values: int  # pixels below 0 or above MAX_PLAUSIBLE_MM
    total_mm: float


def read_communes(path: Path, names: Iterable[str]) -> dict[str, dict]:
    """GeoJSON geometry of each named commune, from a geoBoundaries file."""
    features = json.loads(path.read_text(encoding="utf-8"))["features"]
    by_name = {f["properties"]["shapeName"]: f["geometry"] for f in features}
    names = list(names)
    unknown = [name for name in names if name not in by_name]
    # A misspelt name would silently produce an empty series.
    if unknown:
        raise KeyError(f"communes not in {path.name}: {unknown}")
    return {name: by_name[name] for name in names}


def commune_masks(
    geometries: dict[str, dict], transform: Affine, shape: tuple[int, int]
) -> dict[str, np.ndarray]:
    """Pixels of each commune; a pixel touched by the polygon counts for it."""
    masks = {}
    for name, geometry in geometries.items():
        mask = geometry_mask(
            [geometry],
            out_shape=shape,
            transform=transform,
            invert=True,
            all_touched=True,
        )
        if not mask.any():
            raise ValueError(f"commune {name} has no pixel in the grid")
        masks[name] = mask
    return masks


def band_dates(descriptions: Sequence[str | None], year: int) -> list[date]:
    """Date of each band, from its YYYYMMDD description, else day by day from 1 January."""
    if not any(descriptions):
        return [date(year, 1, 1) + timedelta(days=i) for i in range(len(descriptions))]
    dates = []
    for description in descriptions:
        found = re.search(r"\d{8}", description or "")
        if found is None:
            raise ValueError(f"band without a date: {description!r}")
        day = date(int(found[0][:4]), int(found[0][4:6]), int(found[0][6:]))
        if day.year != year:
            raise ValueError(f"band {day} in the file of {year}")
        dates.append(day)
    if len(set(dates)) != len(dates):
        raise ValueError(f"duplicate band dates in the file of {year}")
    return dates


def commune_rain(
    cube: np.ndarray,
    dates: Sequence[date],
    masks: dict[str, np.ndarray],
    year: int,
    max_mm: float = MAX_PLAUSIBLE_MM,
) -> tuple[list[CommuneDay], list[YearQuality]]:
    """Daily mean of each commune over a (band, row, column) cube, NaN being no data.

    Impossible pixels are counted and left out of the mean, so that one bad
    pixel cannot hide in an average.
    """
    days, quality = [], []
    expected = 366 if calendar.isleap(year) else 365
    for name, mask in masks.items():
        pixels = cube[:, mask]  # (band, pixel)
        finite = np.isfinite(pixels)
        impossible = finite & ((pixels < 0) | (pixels > max_mm))
        valid = finite & ~impossible
        counts = valid.sum(axis=1)
        sums = np.where(valid, pixels, 0.0).sum(axis=1)
        for day, count, total in zip(dates, counts, sums, strict=True):
            mean = float(total / count) if count else None
            days.append(CommuneDay(name, day, mean, int(count)))
        quality.append(
            YearQuality(
                commune=name,
                year=year,
                pixels=int(mask.sum()),
                expected_days=expected,
                missing_days=expected - int((counts > 0).sum()),
                impossible_values=int(impossible.sum()),
                total_mm=float((sums[counts > 0] / counts[counts > 0]).sum()),
            )
        )
    return days, quality


def read_year(
    path: Path,
    year: int,
    geometries: dict[str, dict],
    max_mm: float = MAX_PLAUSIBLE_MM,
) -> tuple[list[CommuneDay], list[YearQuality]]:
    """Commune series and quality counts of one yearly GeoTIFF."""
    with rasterio.open(path) as src:
        # A year is about 7 MB at 0.05 degree over zone A: read it at once.
        cube = src.read(masked=True).astype("float64").filled(np.nan)
        dates = band_dates(src.descriptions, year)
        masks = commune_masks(geometries, src.transform, (src.height, src.width))
    logger.info("%s: %d bands, %d communes", path.name, len(dates), len(masks))
    return commune_rain(cube, dates, masks, year, max_mm)
