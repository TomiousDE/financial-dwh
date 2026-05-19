import psycopg2
from dotenv import load_dotenv
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

def build_exchange_rate_weekly(cur):
    cur.execute("""
        INSERT INTO aggregates.agg_exchange_rate_weekly (
            currency_code, week_start, avg_rate, min_rate, max_rate, volatility
        )
        SELECT
            c.currency_code,
            date_trunc('week', d.full_date)::date AS week_start,
            ROUND(AVG(f.rate_to_ron)::numeric, 6) AS avg_rate,
            ROUND(MIN(f.rate_to_ron)::numeric, 6) AS min_rate,
            ROUND(MAX(f.rate_to_ron)::numeric, 6) AS max_rate,
            ROUND(STDDEV(f.rate_to_ron)::numeric, 6) AS volatility
        FROM dwh.fact_exchange_rates f
        JOIN dwh.dim_date d ON d.date_key = f.date_key
        JOIN dwh.dim_currency c ON c.currency_key = f.currency_key
        GROUP BY c.currency_code, date_trunc('week', d.full_date)::date
        ON CONFLICT (currency_code, week_start) DO UPDATE SET
            avg_rate = EXCLUDED.avg_rate,
            min_rate = EXCLUDED.min_rate,
            max_rate = EXCLUDED.max_rate,
            volatility = EXCLUDED.volatility,
            calculated_at = NOW()
    """)
    print(f"agg_exchange_rate_weekly: {cur.rowcount} înregistrări upserted")

def build_market_monthly(cur):
    cur.execute("""
        INSERT INTO aggregates.agg_market_monthly (
            symbol, year, month, avg_close, min_close, max_close,
            monthly_return_pct, avg_volume
        )
        SELECT
            i.symbol,
            d.year,
            d.month,
            ROUND(AVG(f.close)::numeric, 6) AS avg_close,
            ROUND(MIN(f.close)::numeric, 6) AS min_close,
            ROUND(MAX(f.close)::numeric, 6) AS max_close,
            ROUND(
                ((MAX(f.close) - MIN(f.close)) / NULLIF(MIN(f.close), 0) * 100)::numeric,
                4
            ) AS monthly_return_pct,
            AVG(f.volume)::bigint AS avg_volume
        FROM dwh.fact_market_daily f
        JOIN dwh.dim_date d ON d.date_key = f.date_key
        JOIN dwh.dim_instrument i ON i.instrument_key = f.instrument_key
        GROUP BY i.symbol, d.year, d.month
        ON CONFLICT (symbol, year, month) DO UPDATE SET
            avg_close = EXCLUDED.avg_close,
            min_close = EXCLUDED.min_close,
            max_close = EXCLUDED.max_close,
            monthly_return_pct = EXCLUDED.monthly_return_pct,
            avg_volume = EXCLUDED.avg_volume,
            calculated_at = NOW()
    """)
    print(f"agg_market_monthly: {cur.rowcount} înregistrări upserted")

def build_correlation_monthly(cur):
    cur.execute("""
        INSERT INTO aggregates.agg_correlation_monthly (
            year, month, eur_ron_avg, usd_ron_avg, sp500_avg_close, stoxx_avg_close
        )
        SELECT
            d.year,
            d.month,
            ROUND(AVG(CASE WHEN c.currency_code = 'EUR' THEN f.rate_to_ron END)::numeric, 6) AS eur_ron_avg,
            ROUND(AVG(CASE WHEN c.currency_code = 'USD' THEN f.rate_to_ron END)::numeric, 6) AS usd_ron_avg,
            ROUND(AVG(CASE WHEN i.symbol = '^GSPC' THEN m.close END)::numeric, 6) AS sp500_avg_close,
            ROUND(AVG(CASE WHEN i.symbol = '^STOXX50E' THEN m.close END)::numeric, 6) AS stoxx_avg_close
        FROM dwh.dim_date d
        LEFT JOIN dwh.fact_exchange_rates f ON f.date_key = d.date_key
        LEFT JOIN dwh.dim_currency c ON c.currency_key = f.currency_key
            AND c.currency_code IN ('EUR', 'USD')
        LEFT JOIN dwh.fact_market_daily m ON m.date_key = d.date_key
        LEFT JOIN dwh.dim_instrument i ON i.instrument_key = m.instrument_key
            AND i.symbol IN ('^GSPC', '^STOXX50E')
        WHERE d.full_date <= CURRENT_DATE
        GROUP BY d.year, d.month
        HAVING
            AVG(CASE WHEN c.currency_code = 'EUR' THEN f.rate_to_ron END) IS NOT NULL
        ON CONFLICT (year, month) DO UPDATE SET
            eur_ron_avg = EXCLUDED.eur_ron_avg,
            usd_ron_avg = EXCLUDED.usd_ron_avg,
            sp500_avg_close = EXCLUDED.sp500_avg_close,
            stoxx_avg_close = EXCLUDED.stoxx_avg_close,
            calculated_at = NOW()
    """)
    print(f"agg_correlation_monthly: {cur.rowcount} înregistrări upserted")

def run():
    print("Construire aggregate layers...")
    conn = get_db_connection()
    cur = conn.cursor()

    build_exchange_rate_weekly(cur)
    build_market_monthly(cur)
    build_correlation_monthly(cur)

    conn.commit()
    cur.close()
    conn.close()
    print("Aggregate layer complet.")

if __name__ == "__main__":
    run()