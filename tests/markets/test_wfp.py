from datetime import date

from agritech.markets.wfp import coverage, read_prices

HEADER = (
    "date,admin1,admin2,market,market_id,latitude,longitude,category,commodity,"
    "commodity_id,unit,priceflag,pricetype,currency,price,usdprice\n"
    "#date,#adm1+name,#adm2+name,#loc+market+name,#loc+market+code,#geo+lat,#geo+lon,"
    "#item+type,#item+name,#item+code,#item+unit,#item+price+flag,#item+price+type,"
    "#currency+code,#value,#value+usd\n"
)


def line(day, dept, market, commodity, price_type="Retail", price="250"):
    return (
        f"{day},{dept},Commune,{market},1,9.3,2.6,cereals and tubers,{commodity},"
        f"1,KG,actual,{price_type},XOF,{price},0.4\n"
    )


def write_csv(tmp_path):
    path = tmp_path / "prices.csv"
    path.write_text(
        HEADER
        + line("2026-08-15", "Borgou", "Parakou", "Maize (white)")
        + line("2026-09-15", "Borgou", "Parakou", "Maize (white)")
        + line("2026-09-15", "Littoral", "Dantokpa", "Maize (white)")
        + line("2026-09-15", "Borgou", "Parakou", "Maize", price_type="Wholesale")
        + line("2026-09-15", "Borgou", "Parakou", "Tomatoes"),
        encoding="utf-8",
    )
    return path


def test_read_prices_skips_the_hxl_line(tmp_path):
    rows = list(read_prices(write_csv(tmp_path)))
    assert len(rows) == 5
    assert rows[0].day == date(2026, 8, 15)


def test_coverage_keeps_retail_prices_of_our_crops(tmp_path):
    result = coverage(read_prices(write_csv(tmp_path)))
    # Sorted by crop, commodity, then department: Borgou before Littoral.
    assert [(c.market, c.observations) for c in result] == [
        ("Parakou", 2),
        ("Dantokpa", 1),
    ]
    parakou = result[0]
    assert (parakou.first, parakou.last) == (date(2026, 8, 15), date(2026, 9, 15))


def test_coverage_filters_departments(tmp_path):
    result = coverage(read_prices(write_csv(tmp_path)), {"Borgou"})
    assert {c.market for c in result} == {"Parakou"}
