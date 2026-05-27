from transformation.dim_date_builder import generate_dates
from datetime import date

def test_generate_dates_count():
    dates = generate_dates(date(2026, 1, 1), date(2026, 1, 31))
    assert len(dates) == 31

def test_generate_dates_weekend():
    dates = generate_dates(date(2026, 1, 3), date(2026, 1, 4))
    assert dates[0]["is_weekend"] is True
    assert dates[1]["is_weekend"] is True

def test_generate_dates_weekday():
    dates = generate_dates(date(2026, 1, 5), date(2026, 1, 5))
    assert dates[0]["is_weekend"] is False

def test_generate_dates_quarter():
    dates = generate_dates(date(2026, 4, 1), date(2026, 4, 1))
    assert dates[0]["quarter"] == 2

def test_generate_dates_fields():
    dates = generate_dates(date(2026, 5, 27), date(2026, 5, 27))
    d = dates[0]
    assert d["day"] == 27
    assert d["month"] == 5
    assert d["year"] == 2026
    assert d["day_of_week"] == 2