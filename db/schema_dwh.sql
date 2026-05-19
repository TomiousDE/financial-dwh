CREATE SCHEMA IF NOT EXISTS dwh;

CREATE TABLE IF NOT EXISTS dwh.dim_date (
    date_key        SERIAL PRIMARY KEY,
    full_date       DATE NOT NULL UNIQUE,
    day             SMALLINT NOT NULL,
    month           SMALLINT NOT NULL,
    quarter         SMALLINT NOT NULL,
    year            SMALLINT NOT NULL,
    day_of_week     SMALLINT NOT NULL,
    day_name        VARCHAR(10) NOT NULL,
    month_name      VARCHAR(10) NOT NULL,
    is_weekend      BOOLEAN NOT NULL,
    is_holiday      BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dwh.dim_currency (
    currency_key    SERIAL PRIMARY KEY,
    currency_code   VARCHAR(10) NOT NULL UNIQUE,
    currency_name   VARCHAR(100),
    country         VARCHAR(100),
    region          VARCHAR(50),
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS dwh.dim_instrument (
    instrument_key  SERIAL PRIMARY KEY,
    symbol          VARCHAR(20) NOT NULL UNIQUE,
    name            VARCHAR(200),
    type            VARCHAR(20),
    exchange        VARCHAR(50),
    sector          VARCHAR(100),
    country         VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dwh.fact_exchange_rates (
    rate_id         SERIAL PRIMARY KEY,
    date_key        INT NOT NULL REFERENCES dwh.dim_date(date_key),
    currency_key    INT NOT NULL REFERENCES dwh.dim_currency(currency_key),
    rate_to_ron     NUMERIC(18, 6) NOT NULL,
    source          VARCHAR(20) DEFAULT 'BNR',
    loaded_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(date_key, currency_key)
);

CREATE TABLE IF NOT EXISTS dwh.fact_market_daily (
    market_id       SERIAL PRIMARY KEY,
    date_key        INT NOT NULL REFERENCES dwh.dim_date(date_key),
    instrument_key  INT NOT NULL REFERENCES dwh.dim_instrument(instrument_key),
    open            NUMERIC(18, 6),
    high            NUMERIC(18, 6),
    low             NUMERIC(18, 6),
    close           NUMERIC(18, 6),
    adj_close       NUMERIC(18, 6),
    volume          BIGINT,
    source          VARCHAR(20),
    loaded_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(date_key, instrument_key)
);