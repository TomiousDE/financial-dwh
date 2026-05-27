from datetime import timedelta

from flows.daily_pipeline_flow import daily_pipeline_flow

if __name__ == "__main__":
    daily_pipeline_flow.serve(
        name="daily-financial-pipeline",
        interval=timedelta(days=1),
        tags=["financial", "daily"],
        description="Pipeline zilnic: BNR + yfinance → DWH → Aggregates",
    )
