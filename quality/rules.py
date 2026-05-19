def check_not_null(value, field_name):
    if value is None:
        return False, f"{field_name} este null"
    return True, None

def check_positive(value, field_name):
    if value is None:
        return False, f"{field_name} este null"
    if value <= 0:
        return False, f"{field_name} trebuie să fie pozitiv, găsit: {value}"
    return True, None

def check_rate_range(rate, currency_code):
    if rate is None:
        return False, f"rata pentru {currency_code} este null"
    if rate <= 0:
        return False, f"rata pentru {currency_code} trebuie să fie pozitivă, găsită: {rate}"
    if rate > 100:
        return False, f"rata pentru {currency_code} suspectă de mare: {rate}"
    return True, None

def check_ohlcv(open, high, low, close, volume, symbol):
    errors = []

    for name, val in [("open", open), ("high", high), ("low", low), ("close", close)]:
        ok, msg = check_positive(val, f"{symbol}.{name}")
        if not ok:
            errors.append(msg)

    if high is not None and low is not None and high < low:
        errors.append(f"{symbol}: high ({high}) < low ({low})")

    if open is not None and high is not None and open > high:
        errors.append(f"{symbol}: open ({open}) > high ({high})")

    if close is not None and high is not None and close > high:
        errors.append(f"{symbol}: close ({close}) > high ({high})")

    if volume is not None and volume < 0:
        errors.append(f"{symbol}: volume negativ ({volume})")

    if errors:
        return False, "; ".join(errors)
    return True, None

def validate_bnr_record(record):
    fetched_date, currency_code, rate = record
    ok, msg = check_rate_range(rate, currency_code)
    if not ok:
        return False, msg
    return True, None

def validate_yfinance_record(record):
    fetched_date, symbol, open, high, low, close, adj_close, volume = record
    return check_ohlcv(open, high, low, close, volume, symbol)

METALS = {"XAU", "XAG", "XDR"}

def check_rate_range(rate, currency_code):
    if rate is None:
        return False, f"rata pentru {currency_code} este null"
    if rate <= 0:
        return False, f"rata pentru {currency_code} trebuie să fie pozitivă, găsită: {rate}"
    if currency_code not in METALS and rate > 100:
        return False, f"rata pentru {currency_code} suspectă de mare: {rate}"
    return True, None