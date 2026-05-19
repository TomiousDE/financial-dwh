CREATE SCHEMA IF NOT EXISTS aggregates;

CREATE TABLE IF NOT EXISTS aggregates.agg_exchange_rate_weekly (
    id                  SERIAL PRIMARY KEY,
    currency_code       VARCHAR(10) NOT NULL,
    week_start          DATE NOT NULL,
    avg_rate            NUMERIC(18, 6),
    min_rate            NUMERIC(18, 6),
    max_rate            NUMERIC(18, 6),
    volatility          NUMERIC(18, 6),
    calculated_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(currency_code, week_start)
);

CREATE TABLE IF NOT EXISTS aggregates.agg_market_monthly (
    id                  SERIAL PRIMARY KEY,
    symbol              VARCHAR(20) NOT NULL,
    year                SMALLINT NOT NULL,
    month               SMALLINT NOT NULL,
    avg_close           NUMERIC(18, 6),
    min_close           NUMERIC(18, 6),
    max_close           NUMERIC(18, 6),
    monthly_return_pct  NUMERIC(10, 4),
    avg_volume          BIGINT,
    calculated_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, year, month)
);

CREATE TABLE IF NOT EXISTS aggregates.agg_correlation_monthly (
    id                  SERIAL PRIMARY KEY,
    year                SMALLINT NOT NULL,
    month               SMALLINT NOT NULL,
    eur_ron_avg         NUMERIC(18, 6),
    usd_ron_avg         NUMERIC(18, 6),
    sp500_avg_close     NUMERIC(18, 6),
    stoxx_avg_close     NUMERIC(18, 6),
    calculated_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, month)
);