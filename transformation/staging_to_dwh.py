import psycopg2
from dotenv import load_dotenv
from quality.validator import validate_bnr, validate_yfinance
from quality.anomaly_detector import detect_exchange_rate_anomalies, detect_market_anomalies
import os

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode="disable"
    )

def load_dim_currency(cur):
    cur.execute("""
        INSERT INTO dwh.dim_currency (currency_code)
        SELECT DISTINCT currency_code
        FROM staging.raw_bnr_rates
        ON CONFLICT (currency_code) DO NOTHING
    """)
    print(f"dim_currency: {cur.rowcount} valute noi inserate")

def load_dim_instrument(cur):
    cur.execute("""
        INSERT INTO dwh.dim_instrument (symbol)
        SELECT DISTINCT symbol
        FROM staging.raw_yfinance
        ON CONFLICT (symbol) DO NOTHING
    """)
    print(f"dim_instrument: {cur.rowcount} instrumente noi inserate")

def load_fact_exchange_rates(cur):
    cur.execute("""
        INSERT INTO dwh.fact_exchange_rates (date_key, currency_key, rate_to_ron, source)
        SELECT
            d.date_key,
            c.currency_key,
            r.rate,
            'BNR'
        FROM staging.raw_bnr_rates r
        JOIN dwh.dim_date d ON d.full_date = r.fetched_date
        JOIN dwh.dim_currency c ON c.currency_code = r.currency_code
        ON CONFLICT (date_key, currency_key) DO NOTHING
    """)
    print(f"fact_exchange_rates: {cur.rowcount} înregistrări noi inserate")

def load_fact_market_daily(cur):
    cur.execute("""
        INSERT INTO dwh.fact_market_daily (
            date_key, instrument_key, open, high, low, close, adj_close, volume, source
        )
        SELECT
            d.date_key,
            i.instrument_key,
            r.open,
            r.high,
            r.low,
            r.close,
            r.adj_close,
            r.volume,
            'yfinance'
        FROM staging.raw_yfinance r
        JOIN dwh.dim_date d ON d.full_date = r.fetched_date
        JOIN dwh.dim_instrument i ON i.symbol = r.symbol
        ON CONFLICT (date_key, instrument_key) DO NOTHING
    """)
    print(f"fact_market_daily: {cur.rowcount} înregistrări noi inserate")

def load_fact_market_daily_kaggle(cur):
    cur.execute("""
        INSERT INTO dwh.fact_market_daily (
            date_key, instrument_key, open, high, low, close, adj_close, volume, source
        )
        SELECT
            d.date_key,
            i.instrument_key,
            r.open,
            r.high,
            r.low,
            r.close,
            r.adj_close,
            r.volume,
            'kaggle'
        FROM staging.raw_kaggle r
        JOIN dwh.dim_date d ON d.full_date = r.trade_date
        JOIN dwh.dim_instrument i ON i.symbol = r.symbol
        ON CONFLICT (date_key, instrument_key) DO NOTHING
    """)
    print(f"fact_market_daily (kaggle): {cur.rowcount} înregistrări noi inserate")

def run():
    print("Începere transformare staging → DWH...")
    conn = get_db_connection()
    cur = conn.cursor()

    print("Validare date înainte de încărcare în DWH...")
    bnr_passed, bnr_failed = validate_bnr(cur)
    yf_passed, yf_failed = validate_yfinance(cur)

    if bnr_failed > 0 or yf_failed > 0:
        print(f"⚠️  Avertisment: {bnr_failed + yf_failed} înregistrări invalide detectate. Continuăm doar cu cele valide.")

    load_dim_currency(cur)
    load_dim_instrument(cur)
    load_fact_exchange_rates(cur)
    load_fact_market_daily(cur)
    load_fact_market_daily_kaggle(cur)

    print("Detecție anomalii...")
    detect_exchange_rate_anomalies(cur)
    detect_market_anomalies(cur)

    conn.commit()
    cur.close()
    conn.close()
    print("Transformare completă.")

if __name__ == "__main__":
    run()