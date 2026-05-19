import psycopg2
from dotenv import load_dotenv
from quality.rules import validate_bnr_record, validate_yfinance_record
import os
from datetime import datetime

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

def log_result(cur, table_name, record_id, passed, error_message=None):
    cur.execute("""
        INSERT INTO quality.validation_log (table_name, record_id, passed, error_message, validated_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (table_name, record_id, passed, error_message, datetime.now()))

def validate_bnr(cur):
    cur.execute("""
        SELECT id, fetched_date, currency_code, rate
        FROM staging.raw_bnr_rates
        WHERE id NOT IN (SELECT record_id FROM quality.validation_log WHERE table_name = 'raw_bnr_rates')
    """)
    records = cur.fetchall()

    passed = 0
    failed = 0

    for row in records:
        record_id = row[0]
        record = row[1:]
        ok, msg = validate_bnr_record(record)
        log_result(cur, "raw_bnr_rates", record_id, ok, msg)
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"BNR validation: {passed} passed, {failed} failed")
    return passed, failed

def validate_yfinance(cur):
    cur.execute("""
        SELECT id, fetched_date, symbol, open, high, low, close, adj_close, volume
        FROM staging.raw_yfinance
        WHERE id NOT IN (SELECT record_id FROM quality.validation_log WHERE table_name = 'raw_yfinance')
    """)
    records = cur.fetchall()

    passed = 0
    failed = 0

    for row in records:
        record_id = row[0]
        record = row[1:]
        ok, msg = validate_yfinance_record(record)
        log_result(cur, "raw_yfinance", record_id, ok, msg)
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"yfinance validation: {passed} passed, {failed} failed")
    return passed, failed

def run():
    print("Începere validare date...")
    conn = get_db_connection()
    cur = conn.cursor()

    validate_bnr(cur)
    validate_yfinance(cur)

    conn.commit()
    cur.close()
    conn.close()
    print("Validare completă.")

if __name__ == "__main__":
    run()