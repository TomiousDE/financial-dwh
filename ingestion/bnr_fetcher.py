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

def fetch_bnr_historical(start_year=2015):
    import time
    current_year = date.today().year
    all_rates = []

    for year in range(start_year, current_year + 1):
        url = f"https://www.bnr.ro/files/xml/years/nbrfxrates{year}.xml"
        print(f"Descărcare date BNR pentru {year}...")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            xml_content = response.content

            root = etree.fromstring(xml_content)
            namespace = {"bnr": "http://www.bnr.ro/xsd"}

            for cube in root.findall(".//bnr:Cube", namespace):
                date_str = cube.attrib.get("date")
                if not date_str:
                    continue
                fetched_date = date.fromisoformat(date_str)

                for rate_elem in cube.findall("bnr:Rate", namespace):
                    currency_code = rate_elem.attrib.get("currency")
                    multiplier = int(rate_elem.attrib.get("multiplier", 1))
                    value = float(rate_elem.text)
                    rate = value / multiplier
                    all_rates.append((fetched_date, currency_code, rate, xml_content))

            time.sleep(0.5)

        except Exception as e:
            print(f"Eroare la anul {year}: {e}")
            continue

    return all_rates

def load_historical_to_staging(rates):
    conn = get_db_connection()
    cur = conn.cursor()

    inserted = 0
    skipped = 0

    for fetched_date, currency_code, rate, xml_content in rates:
        cur.execute("""
            INSERT INTO staging.raw_bnr_rates (fetched_date, currency_code, rate, source_xml)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (fetched_date, currency_code, rate, None))

        if cur.rowcount > 0:
            inserted += 1
        else:
            skipped += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"BNR istoric: {inserted} înregistrări inserate, {skipped} sărite")

def run_historical(start_year=2015):
    print(f"Descărcare date istorice BNR din {start_year}...")
    rates = fetch_bnr_historical(start_year)
    print(f"Total parsate: {len(rates)} înregistrări")
    load_historical_to_staging(rates)