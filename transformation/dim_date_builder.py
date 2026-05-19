import psycopg2
from datetime import date, timedelta
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

ROMANIAN_DAYS = {
    0: "Luni", 1: "Marți", 2: "Miercuri",
    3: "Joi", 4: "Vineri", 5: "Sâmbătă", 6: "Duminică"
}

ROMANIAN_MONTHS = {
    1: "Ianuarie", 2: "Februarie", 3: "Martie",
    4: "Aprilie", 5: "Mai", 6: "Iunie",
    7: "Iulie", 8: "August", 9: "Septembrie",
    10: "Octombrie", 11: "Noiembrie", 12: "Decembrie"
}

def generate_dates(start_date, end_date):
    dates = []
    current = start_date
    while current <= end_date:
        dates.append({
            "full_date": current,
            "day": current.day,
            "month": current.month,
            "quarter": (current.month - 1) // 3 + 1,
            "year": current.year,
            "day_of_week": current.weekday(),
            "day_name": ROMANIAN_DAYS[current.weekday()],
            "month_name": ROMANIAN_MONTHS[current.month],
            "is_weekend": current.weekday() >= 5,
            "is_holiday": False
        })
        current += timedelta(days=1)
    return dates

def load_dim_date(start_date, end_date):
    dates = generate_dates(start_date, end_date)

    conn = get_db_connection()
    cur = conn.cursor()

    inserted = 0
    skipped = 0

    for d in dates:
        cur.execute("""
            INSERT INTO dwh.dim_date (
                full_date, day, month, quarter, year,
                day_of_week, day_name, month_name, is_weekend, is_holiday
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (full_date) DO NOTHING
        """, (
            d["full_date"], d["day"], d["month"], d["quarter"], d["year"],
            d["day_of_week"], d["day_name"], d["month_name"],
            d["is_weekend"], d["is_holiday"]
        ))

        if cur.rowcount > 0:
            inserted += 1
        else:
            skipped += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"dim_date: {inserted} date inserate, {skipped} sărite")

def run():
    start_date = date(2015, 1, 1)
    end_date = date(2027, 12, 31)
    print(f"Generare dim_date de la {start_date} la {end_date}...")
    load_dim_date(start_date, end_date)

if __name__ == "__main__":
    run()