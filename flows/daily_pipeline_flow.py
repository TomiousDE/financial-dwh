from prefect import flow, task

from ingestion.bnr_fetcher import run as bnr_run
from ingestion.yfinance_fetcher import run as yfinance_run
from reports.report_generator import run as report_run
from scripts.backup import run_backup
from transformation.aggregates_builder import run as aggregates_run
from transformation.staging_to_dwh import run as transform_run


@task(name="Fetch BNR Rates", retries=3, retry_delay_seconds=60)
def fetch_bnr():
    bnr_run()


@task(name="Fetch yfinance Data", retries=3, retry_delay_seconds=60)
def fetch_yfinance():
    yfinance_run()


@task(name="Transform Staging to DWH", retries=2, retry_delay_seconds=30)
def transform():
    transform_run()


@task(name="Build Aggregates", retries=2, retry_delay_seconds=30)
def build_aggregates():
    aggregates_run()


@task(name="Generate Daily Report", retries=1, retry_delay_seconds=30)
def generate_report():
    report_run()


@task(name="Backup Database", retries=1, retry_delay_seconds=30)
def backup_database():
    run_backup()


@flow(name="Daily Financial Pipeline", log_prints=True)
def daily_pipeline_flow():
    fetch_bnr()
    fetch_yfinance()
    transform()
    build_aggregates()
    generate_report()
    backup_database()


if __name__ == "__main__":
    daily_pipeline_flow()
