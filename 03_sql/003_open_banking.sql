-- Apply after 001_foundation.sql. Public aggregates never join to fictional-bank incidents.
BEGIN;
CREATE TABLE IF NOT EXISTS stg.open_banking_metric (
    batch_id bigint NOT NULL REFERENCES raw.source_batch(batch_id),
    observation_month date NOT NULL,
    metric_name text NOT NULL,
    unit text NOT NULL CHECK (unit IN ('count', 'percent', 'milliseconds')),
    metric_value numeric(20,4) NOT NULL CHECK (metric_value >= 0),
    PRIMARY KEY (batch_id, observation_month, metric_name),
    CHECK (EXTRACT(DAY FROM observation_month) = 1),
    CHECK (unit <> 'percent' OR metric_value <= 100)
);
CREATE INDEX IF NOT EXISTS ix_ob_metric_month ON stg.open_banking_metric(observation_month);

-- Values are percentages on a 0–100 scale; response time is milliseconds.
-- Source rows are already monthly aggregates across reporting organisations.
CREATE OR REPLACE VIEW mart.open_banking_monthly AS
WITH selected_batch AS (
    SELECT DISTINCT ON (m.observation_month) m.observation_month, m.batch_id
    FROM stg.open_banking_metric m
    JOIN raw.source_batch b ON b.batch_id = m.batch_id
    WHERE b.source_name = 'Open Banking API performance'
    ORDER BY m.observation_month, b.retrieved_at DESC, m.batch_id DESC
)
SELECT m.observation_month, max(m.batch_id) AS batch_id,
       max(m.metric_value) FILTER (WHERE m.metric_name = '# of API Calls Successful') AS successful_calls,
       max(m.metric_value) FILTER (WHERE m.metric_name = '# of API Calls Failed') AS failed_calls,
       max(m.metric_value) FILTER (WHERE m.metric_name = '# of API Calls failed for Business Reasons') AS business_failures,
       max(m.metric_value) FILTER (WHERE m.metric_name = '# of API Calls failed for Technical Reasons') AS technical_failures,
       max(m.metric_value) FILTER (WHERE m.metric_name = 'Availability %') AS availability_pct,
       max(m.metric_value) FILTER (WHERE m.metric_name = 'Availability % - Weighted') AS weighted_availability_pct,
       max(m.metric_value) FILTER (WHERE m.metric_name = 'API Response Time') AS response_time_ms,
       count(*) AS source_metrics,
       count(DISTINCT m.batch_id) AS source_batches
FROM stg.open_banking_metric m
JOIN selected_batch sb ON sb.observation_month = m.observation_month
                      AND sb.batch_id = m.batch_id
GROUP BY m.observation_month;
COMMIT;
