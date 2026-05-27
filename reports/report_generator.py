import csv
import os
from datetime import date, datetime

import psycopg2
from dotenv import load_dotenv

load_dotenv()

REPORTS_DIR = "reports/output"


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode="disable",
    )


def get_exchange_rates(cur, report_date):
    cur.execute(
        """
        WITH latest AS (
            SELECT DISTINCT ON (c.currency_code)
                c.currency_code,
                f.rate_to_ron,
                d.full_date,
                f.date_key
            FROM dwh.fact_exchange_rates f
            JOIN dwh.dim_date d ON d.date_key = f.date_key
            JOIN dwh.dim_currency c ON c.currency_key = f.currency_key
            WHERE d.full_date <= %s
            AND c.currency_code IN ('EUR', 'USD', 'GBP', 'CHF')
            ORDER BY c.currency_code, d.full_date DESC
        ),
        prev AS (
            SELECT DISTINCT ON (c.currency_code)
                c.currency_code,
                f.rate_to_ron AS prev_rate
            FROM dwh.fact_exchange_rates f
            JOIN dwh.dim_date d ON d.date_key = f.date_key
            JOIN dwh.dim_currency c ON c.currency_key = f.currency_key
            JOIN latest l ON l.currency_code = c.currency_code
                AND d.full_date < l.full_date
            ORDER BY c.currency_code, d.full_date DESC
        )
        SELECT
            l.currency_code,
            l.rate_to_ron,
            p.prev_rate,
            ROUND(((l.rate_to_ron - p.prev_rate) / NULLIF(p.prev_rate, 0) * 100)::numeric, 4)
        FROM latest l
        LEFT JOIN prev p ON p.currency_code = l.currency_code
        ORDER BY l.currency_code
    """,
        (report_date,),
    )
    return cur.fetchall()


def get_market_data(cur, report_date):
    cur.execute(
        """
        WITH latest AS (
            SELECT DISTINCT ON (i.symbol)
                i.symbol,
                f.close,
                f.volume,
                d.full_date,
                f.instrument_key
            FROM dwh.fact_market_daily f
            JOIN dwh.dim_date d ON d.date_key = f.date_key
            JOIN dwh.dim_instrument i ON i.instrument_key = f.instrument_key
            WHERE d.full_date <= %s
            ORDER BY i.symbol, d.full_date DESC
        ),
        prev AS (
            SELECT DISTINCT ON (i.symbol)
                i.symbol,
                f.close AS prev_close
            FROM dwh.fact_market_daily f
            JOIN dwh.dim_date d ON d.date_key = f.date_key
            JOIN dwh.dim_instrument i ON i.instrument_key = f.instrument_key
            JOIN latest l ON l.symbol = i.symbol
                AND d.full_date < l.full_date
            ORDER BY i.symbol, d.full_date DESC
        )
        SELECT
            l.symbol,
            l.close,
            p.prev_close,
            ROUND(((l.close - p.prev_close) / NULLIF(p.prev_close, 0) * 100)::numeric, 4),
            l.volume
        FROM latest l
        LEFT JOIN prev p ON p.symbol = l.symbol
        ORDER BY l.symbol
    """,
        (report_date,),
    )
    return cur.fetchall()


def get_pipeline_stats(cur, report_date):
    cur.execute(
        """
        SELECT COUNT(*) FROM dwh.fact_exchange_rates f
        JOIN dwh.dim_date d ON d.date_key = f.date_key
        WHERE d.full_date = %s
    """,
        (report_date,),
    )
    bnr_count = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(DISTINCT i.symbol)
        FROM dwh.fact_market_daily f
        JOIN dwh.dim_date d ON d.date_key = f.date_key
        JOIN dwh.dim_instrument i ON i.instrument_key = f.instrument_key
        WHERE d.full_date = (
            SELECT MAX(d2.full_date) FROM dwh.fact_market_daily f2
            JOIN dwh.dim_date d2 ON d2.date_key = f2.date_key
            WHERE d2.full_date <= %s
        )
    """,
        (report_date,),
    )
    market_count = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*), SUM(CASE WHEN passed THEN 1 ELSE 0 END)
        FROM quality.validation_log
        WHERE DATE(validated_at) = %s
    """,
        (report_date,),
    )
    total_validated, total_passed = cur.fetchone()

    cur.execute(
        """
        SELECT COUNT(*) FROM quality.anomaly_log
        WHERE DATE(detected_at) = %s
    """,
        (report_date,),
    )
    anomalies = cur.fetchone()[0]

    return (
        bnr_count,
        market_count,
        total_validated or 0,
        total_passed or 0,
        anomalies or 0,
    )


def generate_html(
    report_date,
    rates,
    market,
    bnr_count,
    market_count,
    total_validated,
    total_passed,
    anomalies,
):
    os.makedirs(REPORTS_DIR, exist_ok=True)

    def arrow(val):
        if val is None:
            return ""
        return "▲" if val > 0 else "▼" if val < 0 else "–"

    def color(val):
        if val is None:
            return "black"
        return "green" if val > 0 else "red" if val < 0 else "black"

    rates_rows = ""
    for code, rate, prev, chg in rates:
        rates_rows += f"""
        <tr>
            <td><strong>{code}</strong></td>
            <td>{rate:.4f} RON</td>
            <td style="color:{color(chg)}">{arrow(chg)} {f"{chg:.2f}%" if chg is not None else "N/A"}</td>
        </tr>"""

    market_rows = ""
    for symbol, close, prev, chg, volume in market:
        market_rows += f"""
        <tr>
            <td><strong>{symbol}</strong></td>
            <td>{close:.2f}</td>
            <td style="color:{color(chg)}">{arrow(chg)} {f"{chg:.2f}%" if chg is not None else "N/A"}</td>
            <td>{f"{volume:,}" if volume else "N/A"}</td>
        </tr>"""

    quality_pct = round(total_passed / total_validated * 100, 1) if total_validated > 0 else 100.0

    html = f"""<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <title>Raport Zilnic – {report_date}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; color: #333; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #2980b9; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th {{ background: #3498db; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f5f5f5; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
        .kpi {{ background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; border-radius: 4px; }}
        .kpi-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .kpi-label {{ font-size: 12px; color: #777; margin-top: 4px; }}
        .footer {{ margin-top: 40px; color: #999; font-size: 12px; text-align: center; }}
        .anomaly {{ border-left-color: #e74c3c; }}
    </style>
</head>
<body>
    <h1>📊 Raport Zilnic Financial DWH</h1>
    <p>Data: <strong>{report_date}</strong> | Generat la: {datetime.now().strftime("%H:%M:%S")}</p>

    <div class="kpi-grid">
        <div class="kpi">
            <div class="kpi-value">{bnr_count}</div>
            <div class="kpi-label">Cursuri BNR procesate</div>
        </div>
        <div class="kpi">
            <div class="kpi-value">{market_count}</div>
            <div class="kpi-label">Instrumente procesate</div>
        </div>
        <div class="kpi">
            <div class="kpi-value">{quality_pct}%</div>
            <div class="kpi-label">Data Quality</div>
        </div>
        <div class="kpi {"anomaly" if anomalies > 0 else ""}">
            <div class="kpi-value">{anomalies}</div>
            <div class="kpi-label">Anomalii detectate</div>
        </div>
    </div>

    <h2>💱 Cursuri Valutare</h2>
    <table>
        <tr><th>Valută</th><th>Curs RON</th><th>Variație</th></tr>
        {rates_rows}
    </table>

    <h2>📈 Piețe Financiare</h2>
    <table>
        <tr><th>Simbol</th><th>Închidere</th><th>Variație</th><th>Volum</th></tr>
        {market_rows}
    </table>

    <div class="footer">
        Financial DWH | Generat automat de pipeline-ul Prefect
    </div>
</body>
</html>"""

    filename = f"{REPORTS_DIR}/report_{report_date}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Raport HTML generat: {filename}")
    return filename


def generate_csv(
    report_date,
    rates,
    market,
    bnr_count,
    market_count,
    total_validated,
    total_passed,
    anomalies,
):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filename = f"{REPORTS_DIR}/report_{report_date}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["RAPORT ZILNIC FINANCIAL DWH"])
        writer.writerow(["Data", report_date])
        writer.writerow(["Generat la", datetime.now().strftime("%H:%M:%S")])
        writer.writerow([])

        writer.writerow(["PIPELINE STATS"])
        writer.writerow(["Metric", "Valoare"])
        writer.writerow(["Cursuri BNR procesate", bnr_count])
        writer.writerow(["Instrumente procesate", market_count])
        writer.writerow(["Inregistrari validate", total_validated])
        writer.writerow(["Inregistrari trecute", total_passed])
        writer.writerow(["Anomalii detectate", anomalies])
        writer.writerow([])

        writer.writerow(["CURSURI VALUTARE"])
        writer.writerow(["Valuta", "Curs RON", "Variatie %"])
        for code, rate, prev, chg in rates:
            writer.writerow([code, round(float(rate), 4), round(float(chg), 2) if chg else "N/A"])
        writer.writerow([])

        writer.writerow(["PIETE FINANCIARE"])
        writer.writerow(["Simbol", "Inchidere", "Variatie %", "Volum"])
        for symbol, close, prev, chg, volume in market:
            writer.writerow(
                [
                    symbol,
                    round(float(close), 2),
                    round(float(chg), 2) if chg else "N/A",
                    volume or "N/A",
                ]
            )

    print(f"Raport CSV generat: {filename}")
    return filename


def run(report_date=None):
    if report_date is None:
        report_date = date.today()

    print(f"Generare raport pentru {report_date}...")
    conn = get_db_connection()
    cur = conn.cursor()

    rates = get_exchange_rates(cur, report_date)
    market = get_market_data(cur, report_date)
    bnr_count, market_count, total_validated, total_passed, anomalies = get_pipeline_stats(cur, report_date)

    cur.close()
    conn.close()

    generate_html(
        report_date,
        rates,
        market,
        bnr_count,
        market_count,
        total_validated,
        total_passed,
        anomalies,
    )
    generate_csv(
        report_date,
        rates,
        market,
        bnr_count,
        market_count,
        total_validated,
        total_passed,
        anomalies,
    )
    print("Rapoarte generate cu succes.")


if __name__ == "__main__":
    run()
