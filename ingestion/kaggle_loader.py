import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

CSV_PATH = "data/all_stocks_5yr.csv"

SYMBOLS_TO_LOAD = ["AAPL", "MSFT", "GOOGL"]

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode="disable"
    )

def load_csv():
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.lower()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df[df["Name"].isin(SYMBOLS_TO_LOAD)] if "Name" in df.columns else df[df["name"].isin(SYMBOLS_TO_LOAD)]
    df = df.rename(columns={"Name": "name"}) if "Name" in df.columns else df
    print(f"CSV încărcat: {len(df)} rânduri pentru {SYMBOLS_TO_LOAD}")
    return df

def load_to_staging(df):
    conn = get_db_connection()
    cur = conn.cursor()

    inserted = 0
    skipped = 0

    for _, row in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO staging.raw_kaggle (trade_date, symbol, open, high, low, close, adj_close, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                row["date"],
                row["name"],
                float(row["open"]) if pd.notna(row["open"]) else None,
                float(row["high"]) if pd.notna(row["high"]) else None,
                float(row["low"]) if pd.notna(row["low"]) else None,
                float(row["close"]) if pd.notna(row["close"]) else None,
                float(row["close"]) if pd.notna(row["close"]) else None,
                int(row["volume"]) if pd.notna(row["volume"]) else None,
            ))

            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        except Exception as e:
            print(f"Eroare la rândul {row}: {e}")
            continue

    conn.commit()
    cur.close()
    conn.close()
    print(f"Kaggle: {inserted} înregistrări inserate, {skipped} sărite")

def run():
    print("Încărcare date istorice Kaggle...")
    df = load_csv()
    load_to_staging(df)

if __name__ == "__main__":
    run()