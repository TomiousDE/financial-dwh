import yfinance as yf
import psycopg2
from datetime import date, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

SYMBOLS = ["^GSPC", "^STOXX50E", "AAPL", "MSFT", "GOOGL"]

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode="disable"
    )

def fetch_latest(symbol):
    end = date.today()
    start = end - timedelta(days=5)
    df = yf.download(symbol, start=start, end=end, auto_adjust=True, progress=False)
    return df

def load_to_staging(symbol, df):
    if df.empty:
        print(f"{symbol}: nu s-au găsit date")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    inserted = 0
    skipped = 0

    for idx, row in df.iterrows():
        fetched_date = idx.date()

        cur.execute("""
            INSERT INTO staging.raw_yfinance (fetched_date, symbol, open, high, low, close, adj_close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            fetched_date,
            symbol,
            float(row["Open"].iloc[0]) if hasattr(row["Open"], "iloc") else float(row["Open"]),
            float(row["High"].iloc[0]) if hasattr(row["High"], "iloc") else float(row["High"]),
            float(row["Low"].iloc[0]) if hasattr(row["Low"], "iloc") else float(row["Low"]),
            float(row["Close"].iloc[0]) if hasattr(row["Close"], "iloc") else float(row["Close"]),
            float(row["Close"].iloc[0]) if hasattr(row["Close"], "iloc") else float(row["Close"]),
            int(row["Volume"].iloc[0]) if hasattr(row["Volume"], "iloc") else int(row["Volume"]),
        ))

        if cur.rowcount > 0:
            inserted += 1
        else:
            skipped += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"{symbol}: {inserted} înregistrări inserate, {skipped} sărite")

def run():
    for symbol in SYMBOLS:
        print(f"Descărcare date pentru {symbol}...")
        df = fetch_latest(symbol)
        load_to_staging(symbol, df)

if __name__ == "__main__":
    run()