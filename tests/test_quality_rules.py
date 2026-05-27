from quality.rules import (
    validate_bnr_record,
    validate_yfinance_record,
    check_rate_range
)
from datetime import date

def test_bnr_valid_record():
    record = (date(2026, 1, 1), "EUR", 5.2)
    ok, msg = validate_bnr_record(record)
    assert ok is True
    assert msg is None

def test_bnr_negative_rate():
    record = (date(2026, 1, 1), "EUR", -1.0)
    ok, msg = validate_bnr_record(record)
    assert ok is False

def test_bnr_null_rate():
    record = (date(2026, 1, 1), "EUR", None)
    ok, msg = validate_bnr_record(record)
    assert ok is False

def test_bnr_suspicious_rate():
    record = (date(2026, 1, 1), "EUR", 200.0)
    ok, msg = validate_bnr_record(record)
    assert ok is False

def test_bnr_gold_rate():
    record = (date(2026, 1, 1), "XAU", 656.0)
    ok, msg = validate_bnr_record(record)
    assert ok is True

def test_yfinance_valid_record():
    record = (date(2026, 1, 1), "AAPL", 150.0, 155.0, 148.0, 152.0, 152.0, 1000000)
    ok, msg = validate_yfinance_record(record)
    assert ok is True

def test_yfinance_high_less_than_low():
    record = (date(2026, 1, 1), "AAPL", 150.0, 140.0, 155.0, 152.0, 152.0, 1000000)
    ok, msg = validate_yfinance_record(record)
    assert ok is False

def test_yfinance_negative_price():
    record = (date(2026, 1, 1), "AAPL", -1.0, 155.0, 148.0, 152.0, 152.0, 1000000)
    ok, msg = validate_yfinance_record(record)
    assert ok is False

def test_yfinance_negative_volume():
    record = (date(2026, 1, 1), "AAPL", 150.0, 155.0, 148.0, 152.0, 152.0, -100)
    ok, msg = validate_yfinance_record(record)
    assert ok is False