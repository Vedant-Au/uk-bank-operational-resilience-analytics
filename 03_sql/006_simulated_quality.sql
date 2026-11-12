-- Read-only checks for the fictional bank. No joins to public API metrics.
SELECT b.batch_id, b.source_kind, count(DISTINCT r.row_number) AS raw_rows,
       (SELECT count(*) FROM stg.service) AS services,
       (SELECT count(*) FROM stg.supplier) AS suppliers,
       (SELECT count(*) FROM stg.service_supplier) AS dependencies,
       (SELECT count(*) FROM stg.supplier_observation) AS monthly_observations,
       (SELECT count(*) FROM stg.incident) AS incident_impact_rows,
       (SELECT count(*) FROM core.fact_incident) AS core_incident_impact_rows
FROM raw.source_batch b JOIN raw.source_row r ON r.batch_id=b.batch_id
WHERE b.source_kind='simulated_internal' GROUP BY b.batch_id,b.source_kind;

-- All these exception queries should return zero rows.
SELECT i.incident_id FROM stg.incident i
LEFT JOIN stg.service_supplier d ON d.service_id=i.service_id AND d.supplier_id=i.supplier_id
WHERE i.supplier_id IS NOT NULL AND d.supplier_id IS NULL;

SELECT shared_event_id, count(*) AS impacts, count(DISTINCT supplier_id) AS suppliers
FROM stg.incident WHERE shared_event_id IS NOT NULL
GROUP BY shared_event_id HAVING count(*) < 2 OR count(DISTINCT supplier_id) <> 1;

SELECT supplier_id, count(*) AS months
FROM stg.supplier_observation GROUP BY supplier_id HAVING count(*) <> 24;

-- Mart describes synthetic service impacts, not independent root events.
SELECT service_id, service_name, incident_count, tolerance_breach_count,
       median_duration_minutes, incident_loss_gbp_sum
FROM mart.service_incident_summary ORDER BY service_id;
