import requests
import psycopg2
from lxml import etree
from datetime import date
from dotenv import load_dotenv
import os

load_dotenv()

BNR_URL = "https://www.bnr.ro/nbrfxrates.xml"

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode="disable"
    )

def fetch_bnr_xml():
    response = requests.get(BNR_URL, timeout=10)
    response.raise_for_status()
    return response.content

def parse_bnr_xml(xml_content):
    root = etree.fromstring(xml_content)
    namespace = {"bnr": "http://www.bnr.ro/xsd"}

    cube = root.find(".//bnr:Cube/bnr:Rate/..", namespace)
    if cube is None:
        raise ValueError("Nu s-au găsit date în XML-ul BNR")

    fetched_date_str = cube.attrib.get("date")
    fetched_date = date.fromisoformat(fetched_date_str)

    rates = []
    for rate_elem in cube.findall("bnr:Rate", namespace):
        currency_code = rate_elem.attrib.get("currency")
        multiplier = int(rate_elem.attrib.get("multiplier", 1))
        value = float(rate_elem.text)
        rate = value / multiplier
        rates.append((fetched_date, currency_code, rate))

    return rates

def load_to_staging(rates, xml_content):
    conn = get_db_connection()
    cur = conn.cursor()

    inserted = 0
    skipped = 0

    for fetched_date, currency_code, rate in rates:
        cur.execute("""
            INSERT INTO staging.raw_bnr_rates (fetched_date, currency_code, rate, source_xml)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (fetched_date, currency_code, rate, xml_content.decode("utf-8")))

        if cur.rowcount > 0:
            inserted += 1
        else:
            skipped += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"BNR: {inserted} înregistrări inserate, {skipped} sărite (deja existente)")

def run():
    print("Descărcare date BNR...")
    xml_content = fetch_bnr_xml()
    rates = parse_bnr_xml(xml_content)
    print(f"Parsate {len(rates)} valute pentru data {rates[0][0]}")
    load_to_staging(rates, xml_content)

if __name__ == "__main__":
    run()