-- Read-only checks; psql's ON_ERROR_STOP=1 makes execution failures visible.
SELECT table_schema, count(*) AS table_count
FROM information_schema.tables
WHERE table_schema IN ('raw', 'stg', 'core', 'mart')
  AND table_type = 'BASE TABLE'
GROUP BY table_schema ORDER BY table_schema;
SELECT count(*) AS simulated_incident_count FROM core.fact_incident;
SELECT * FROM mart.service_incident_summary LIMIT 5;
