import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode="disable",
    )


def detect_exchange_rate_anomalies(cur):
    cur.execute("""
        WITH stats AS (
            SELECT
                c.currency_code,
                d.full_date,
                f.rate_to_ron,
                AVG(f.rate_to_ron) OVER (
                    PARTITION BY c.currency_code
                    ORDER BY d.full_date
                    ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
                ) AS mean_30d,
                STDDEV(f.rate_to_ron) OVER (
                    PARTITION BY c.currency_code
                    ORDER BY d.full_date
                    ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
                ) AS std_30d
            FROM dwh.fact_exchange_rates f
            JOIN dwh.dim_date d ON d.date_key = f.date_key
            JOIN dwh.dim_currency c ON c.currency_key = f.currency_key
        )
        INSERT INTO quality.anomaly_log
            (source, entity, metric, value_date, actual_value, mean_30d, std_30d, deviation)
        SELECT
            'BNR',
            currency_code,
            'rate_to_ron',
            full_date,
            rate_to_ron,
            mean_30d,
            std_30d,
            ROUND((ABS(rate_to_ron - mean_30d) / NULLIF(std_30d, 0))::numeric, 4)
        FROM stats
        WHERE
            mean_30d IS NOT NULL
            AND std_30d IS NOT NULL
            AND std_30d > 0
            AND ABS(rate_to_ron - mean_30d) / NULLIF(std_30d, 0) > 3
            AND full_date NOT IN (
                SELECT value_date FROM quality.anomaly_log
                WHERE source = 'BNR' AND entity = currency_code
            )
    """)
    print(f"Anomalii BNR detectate: {cur.rowcount}")


def detect_market_anomalies(cur):
    cur.execute("""
        WITH stats AS (
            SELECT
                i.symbol,
                d.full_date,
                f.close,
                f.volume,
                AVG(f.close) OVER (
                    PARTITION BY i.symbol
                    ORDER BY d.full_date
                    ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
                ) AS mean_close_30d,
                STDDEV(f.close) OVER (
                    PARTITION BY i.symbol
                    ORDER BY d.full_date
                    ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
                ) AS std_close_30d,
                AVG(f.volume) OVER (
                    PARTITION BY i.symbol
                    ORDER BY d.full_date
                    ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
                ) AS mean_volume_30d,
                STDDEV(f.volume) OVER (
                    PARTITION BY i.symbol
                    ORDER BY d.full_date
                    ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
                ) AS std_volume_30d
            FROM dwh.fact_market_daily f
            JOIN dwh.dim_date d ON d.date_key = f.date_key
            JOIN dwh.dim_instrument i ON i.instrument_key = f.instrument_key
        )
        INSERT INTO quality.anomaly_log
            (source, entity, metric, value_date, actual_value, mean_30d, std_30d, deviation)
        SELECT
            'yfinance',
            symbol,
            'close',
            full_date,
            close,
            mean_close_30d,
            std_close_30d,
            ROUND((ABS(close - mean_close_30d) / NULLIF(std_close_30d, 0))::numeric, 4)
        FROM stats
        WHERE
            mean_close_30d IS NOT NULL
            AND std_close_30d IS NOT NULL
            AND std_close_30d > 0
            AND ABS(close - mean_close_30d) / NULLIF(std_close_30d, 0) > 3
            AND full_date NOT IN (
                SELECT value_date FROM quality.anomaly_log
                WHERE source = 'yfinance' AND entity = symbol
            )
    """)
    print(f"Anomalii market detectate: {cur.rowcount}")


def run():
    print("Detecție anomalii...")
    conn = get_db_connection()
    cur = conn.cursor()

    detect_exchange_rate_anomalies(cur)
    detect_market_anomalies(cur)

    conn.commit()
    cur.close()
    conn.close()
    print("Detecție anomalii completă.")


if __name__ == "__main__":
    run()
