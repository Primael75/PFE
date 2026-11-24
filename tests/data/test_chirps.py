"""CHIRPS per commune, on a tiny GeoTIFF written like the Earth Engine exports."""

import json
from datetime import date, timedelta

import pytest

np = pytest.importorskip("numpy")
rasterio = pytest.importorskip("rasterio")

from rasterio.transform import from_origin

from agritech.data.chirps import band_dates, read_communes, read_year

PIXEL = 0.05
WEST, NORTH = 2.0, 10.0


def square(col0, col1, row0, row1):
    """Polygon covering whole pixels, slightly inside so that only they are touched."""
    e = PIXEL / 10
    x0, x1 = WEST + col0 * PIXEL + e, WEST + col1 * PIXEL - e
    y0, y1 = NORTH - row1 * PIXEL + e, NORTH - row0 * PIXEL - e
    return {
        "type": "Polygon",
        "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]],
    }


@pytest.fixture
def boundaries(tmp_path):
    path = tmp_path / "boundaries.geojson"
    features = [
        {"properties": {"shapeName": "West"}, "geometry": square(0, 2, 0, 2)},
        {"properties": {"shapeName": "East"}, "geometry": square(2, 4, 0, 2)},
    ]
    path.write_text(json.dumps({"features": features}), encoding="utf-8")
    return path


def write_year(path, year, cube, dates):
    profile = {
        "driver": "GTiff",
        "width": cube.shape[2],
        "height": cube.shape[1],
        "count": cube.shape[0],
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": from_origin(WEST, NORTH, PIXEL, PIXEL),
        "compress": "lzw",
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(cube.astype("float32"))
        for i, day in enumerate(dates, start=1):
            dst.set_band_description(i, f"{day:%Y%m%d}")


def year_cube(year, skip=()):
    first = date(year, 1, 1)
    days = (date(year + 1, 1, 1) - first).days
    dates = [first + timedelta(days=i) for i in range(days) if i not in skip]
    cube = np.full((len(dates), 2, 4), 2.0)  # 2 rows x 4 columns, 2 mm everywhere
    return cube, dates


def test_daily_mean_per_commune(tmp_path, boundaries):
    cube, dates = year_cube(2001)
    cube[0, :, 2:] = [[1.0, 3.0], [5.0, 7.0]]  # East on 1 January: mean 4 mm
    write_year(tmp_path / "y.tif", 2001, cube, dates)
    days, quality = read_year(
        tmp_path / "y.tif", 2001, read_communes(boundaries, ["East"])
    )
    assert (days[0].day, days[0].rain_mm, days[0].valid_pixels) == (
        date(2001, 1, 1),
        4.0,
        4,
    )
    assert quality[0].pixels == 4
    assert quality[0].total_mm == pytest.approx(4.0 + 364 * 2.0)


def test_impossible_pixels_are_counted_and_left_out(tmp_path, boundaries):
    cube, dates = year_cube(2001)
    cube[0, 0, 0] = -5.0  # an average over West would hide it
    cube[1, 0, 0] = 900.0
    write_year(tmp_path / "y.tif", 2001, cube, dates)
    days, quality = read_year(
        tmp_path / "y.tif", 2001, read_communes(boundaries, ["West"])
    )
    assert quality[0].impossible_values == 2
    assert (days[0].rain_mm, days[0].valid_pixels) == (2.0, 3)
    assert quality[0].missing_days == 0


def test_absent_band_and_empty_day_are_missing_days(tmp_path, boundaries):
    cube, dates = year_cube(2004, skip={59})  # no band for 29 February
    cube[10, :, :2] = np.nan  # West has no valid pixel on 11 January
    write_year(tmp_path / "y.tif", 2004, cube, dates)
    days, quality = read_year(
        tmp_path / "y.tif", 2004, read_communes(boundaries, ["West"])
    )
    assert quality[0].expected_days == 366
    assert quality[0].missing_days == 2
    assert days[10].rain_mm is None  # missing, never zero


def test_misspelt_commune_is_an_error(boundaries):
    with pytest.raises(KeyError, match="Wset"):
        read_communes(boundaries, ["West", "Wset"])


def test_band_dates_without_descriptions_count_from_1_january():
    assert band_dates([None, None], 2001) == [date(2001, 1, 1), date(2001, 1, 2)]


def test_band_of_another_year_is_an_error():
    with pytest.raises(ValueError, match="2001"):
        band_dates(["20020101"], 2001)
