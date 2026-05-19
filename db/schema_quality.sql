CREATE SCHEMA IF NOT EXISTS quality;

CREATE TABLE IF NOT EXISTS quality.validation_log (
    id              SERIAL PRIMARY KEY,
    table_name      VARCHAR(100) NOT NULL,
    record_id       INT NOT NULL,
    passed          BOOLEAN NOT NULL,
    error_message   TEXT,
    validated_at    TIMESTAMP DEFAULT NOW()
);