CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.raw_bnr_rates (
    id              SERIAL PRIMARY KEY,
    fetched_date    DATE NOT NULL,
    currency_code   VARCHAR(10) NOT NULL,
    rate            NUMERIC(18, 6) NOT NULL,
    source_xml      TEXT,
    loaded_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.raw_yfinance (
    id              SERIAL PRIMARY KEY,
    fetched_date    DATE NOT NULL,
    symbol          VARCHAR(20) NOT NULL,
    open            NUMERIC(18, 6),
    high            NUMERIC(18, 6),
    low             NUMERIC(18, 6),
    close           NUMERIC(18, 6),
    adj_close       NUMERIC(18, 6),
    volume          BIGINT,
    loaded_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.raw_kaggle (
    id              SERIAL PRIMARY KEY,
    trade_date      DATE NOT NULL,
    symbol          VARCHAR(20) NOT NULL,
    open            NUMERIC(18, 6),
    high            NUMERIC(18, 6),
    low             NUMERIC(18, 6),
    close           NUMERIC(18, 6),
    adj_close       NUMERIC(18, 6),
    volume          BIGINT,
    loaded_at       TIMESTAMP DEFAULT NOW()
);