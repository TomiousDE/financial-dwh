CREATE SCHEMA IF NOT EXISTS quality;

CREATE TABLE IF NOT EXISTS quality.validation_log (
    id              SERIAL PRIMARY KEY,
    table_name      VARCHAR(100) NOT NULL,
    record_id       INT NOT NULL,
    passed          BOOLEAN NOT NULL,
    error_message   TEXT,
    validated_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quality.anomaly_log (
    id              SERIAL PRIMARY KEY,
    detected_at     TIMESTAMP DEFAULT NOW(),
    source          VARCHAR(20),
    entity          VARCHAR(20),
    metric          VARCHAR(20),
    value_date      DATE,
    actual_value    NUMERIC(18, 6),
    mean_30d        NUMERIC(18, 6),
    std_30d         NUMERIC(18, 6),
    deviation       NUMERIC(10, 4),
    is_resolved     BOOLEAN DEFAULT FALSE
);