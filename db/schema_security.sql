-- Rol read-only pentru dashboard Power BI
CREATE ROLE dwh_reader WITH LOGIN PASSWORD 'reader_password';
GRANT CONNECT ON DATABASE financial_dwh TO dwh_reader;
GRANT USAGE ON SCHEMA dwh, aggregates TO dwh_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA dwh TO dwh_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA aggregates TO dwh_reader;

-- Rol pentru pipeline Prefect
CREATE ROLE dwh_pipeline WITH LOGIN PASSWORD 'pipeline_password';
GRANT CONNECT ON DATABASE financial_dwh TO dwh_pipeline;
GRANT USAGE ON SCHEMA staging, dwh, quality, aggregates TO dwh_pipeline;
GRANT ALL ON ALL TABLES IN SCHEMA staging TO dwh_pipeline;
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA dwh TO dwh_pipeline;
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA quality TO dwh_pipeline;
GRANT INSERT, UPDATE ON ALL TABLES IN SCHEMA aggregates TO dwh_pipeline;