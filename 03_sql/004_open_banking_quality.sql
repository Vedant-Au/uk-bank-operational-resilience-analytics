-- Read-only source-to-mart checks. Run with psql -P pager=off.
WITH source_counts AS (
    SELECT b.batch_id,
           count(DISTINCT r.row_number) AS raw_metric_rows,
           count(m.metric_name) AS typed_observations,
           count(DISTINCT m.observation_month) AS months,
           count(DISTINCT m.metric_name) AS metrics,
           min(m.observation_month) AS first_month,
           max(m.observation_month) AS last_month
    FROM raw.source_batch b
    LEFT JOIN raw.source_row r ON r.batch_id = b.batch_id
    LEFT JOIN stg.open_banking_metric m ON m.batch_id = b.batch_id
          AND r.payload ->> 'Values' = m.metric_name
    WHERE b.source_name = 'Open Banking API performance'
    GROUP BY b.batch_id
), reconciliation AS (
    SELECT count(*) FILTER (WHERE failed_calls <> business_failures + technical_failures)
             AS months_with_failure_split_error,
           count(*) FILTER (WHERE source_metrics <> 20 OR source_batches <> 1)
             AS months_with_incomplete_selected_batch
    FROM mart.open_banking_monthly
)
SELECT s.batch_id, s.raw_metric_rows, s.typed_observations,
       s.months, s.metrics, s.first_month, s.last_month,
       r.months_with_failure_split_error,
       r.months_with_incomplete_selected_batch
FROM source_counts s CROSS JOIN reconciliation r
ORDER BY s.batch_id;

-- Independent raw row count (the join above expands each source row by month).
SELECT batch_id, count(*) AS raw_rows
FROM raw.source_row
GROUP BY batch_id ORDER BY batch_id;

-- Every aggregate month should contain the same number of published metrics.
SELECT observation_month, count(*) AS metrics
FROM stg.open_banking_metric
GROUP BY observation_month HAVING count(*) <> 20
ORDER BY observation_month;
