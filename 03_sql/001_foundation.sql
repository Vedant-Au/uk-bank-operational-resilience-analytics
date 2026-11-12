-- PostgreSQL 15+. Run against an empty, dedicated risk_analytics database.
-- No invented records are inserted. Source and simulated layers remain separate.
BEGIN;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS raw.source_batch (
    batch_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name text NOT NULL,
    source_kind text NOT NULL CHECK (source_kind IN ('public', 'simulated_internal')),
    source_url text,
    source_file text NOT NULL,
    sha256 char(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    retrieved_at timestamptz NOT NULL DEFAULT now(),
    coverage_start date,
    coverage_end date,
    license_note text,
    CHECK (coverage_end IS NULL OR coverage_start IS NULL OR coverage_end >= coverage_start)
);

-- Keep source rows unchanged; typed staging is derived, never a replacement.
CREATE TABLE IF NOT EXISTS raw.source_row (
    batch_id bigint NOT NULL REFERENCES raw.source_batch(batch_id),
    row_number bigint NOT NULL CHECK (row_number > 0),
    payload jsonb NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (batch_id, row_number)
);

CREATE TABLE IF NOT EXISTS stg.service (
    service_id text PRIMARY KEY,
    service_name text NOT NULL UNIQUE,
    impact_tolerance_minutes integer NOT NULL CHECK (impact_tolerance_minutes > 0),
    criticality text NOT NULL CHECK (criticality IN ('high', 'medium', 'low')),
    batch_id bigint NOT NULL REFERENCES raw.source_batch(batch_id)
);
CREATE TABLE IF NOT EXISTS stg.supplier (
    supplier_id text PRIMARY KEY,
    supplier_name text NOT NULL UNIQUE,
    supplier_type text NOT NULL,
    substitutability text NOT NULL CHECK (substitutability IN ('high', 'medium', 'low')),
    batch_id bigint NOT NULL REFERENCES raw.source_batch(batch_id)
);
CREATE TABLE IF NOT EXISTS stg.service_supplier (
    service_id text NOT NULL REFERENCES stg.service(service_id),
    supplier_id text NOT NULL REFERENCES stg.supplier(supplier_id),
    valid_from date NOT NULL,
    valid_to date,
    PRIMARY KEY (service_id, supplier_id, valid_from),
    CHECK (valid_to IS NULL OR valid_to >= valid_from)
);
CREATE TABLE IF NOT EXISTS stg.incident (
    incident_id text PRIMARY KEY,
    shared_event_id text,
    service_id text NOT NULL REFERENCES stg.service(service_id),
    supplier_id text REFERENCES stg.supplier(supplier_id),
    started_at timestamptz NOT NULL,
    restored_at timestamptz NOT NULL,
    detected_at timestamptz,
    incident_type text NOT NULL,
    severity text NOT NULL CHECK (severity IN ('high', 'medium', 'low')),
    customers_affected bigint CHECK (customers_affected >= 0),
    loss_gbp numeric(16,2) CHECK (loss_gbp >= 0),
    batch_id bigint NOT NULL REFERENCES raw.source_batch(batch_id),
    CHECK (restored_at >= started_at),
    CHECK (detected_at IS NULL OR detected_at BETWEEN started_at AND restored_at)
);
CREATE TABLE IF NOT EXISTS stg.supplier_observation (
    supplier_id text NOT NULL REFERENCES stg.supplier(supplier_id),
    observation_date date NOT NULL,
    availability_pct numeric(6,3) CHECK (availability_pct BETWEEN 0 AND 100),
    warning_indicator boolean,
    batch_id bigint NOT NULL REFERENCES raw.source_batch(batch_id),
    PRIMARY KEY (supplier_id, observation_date)
);

-- Core dimensions are deliberately narrow until source profiling fixes grains.
CREATE TABLE IF NOT EXISTS core.dim_service (
    service_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_id text NOT NULL UNIQUE,
    service_name text NOT NULL,
    impact_tolerance_minutes integer NOT NULL CHECK (impact_tolerance_minutes > 0)
);
CREATE TABLE IF NOT EXISTS core.dim_supplier (
    supplier_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    supplier_id text NOT NULL UNIQUE,
    supplier_name text NOT NULL,
    supplier_type text NOT NULL
);
CREATE TABLE IF NOT EXISTS core.fact_incident (
    incident_id text PRIMARY KEY,
    shared_event_id text,
    service_key bigint NOT NULL REFERENCES core.dim_service(service_key),
    supplier_key bigint REFERENCES core.dim_supplier(supplier_key),
    started_at timestamptz NOT NULL,
    restored_at timestamptz NOT NULL,
    duration_minutes numeric(12,2) GENERATED ALWAYS AS
        (EXTRACT(EPOCH FROM (restored_at - started_at)) / 60.0) STORED,
    customers_affected bigint CHECK (customers_affected >= 0),
    loss_gbp numeric(16,2) CHECK (loss_gbp >= 0),
    batch_id bigint NOT NULL REFERENCES raw.source_batch(batch_id),
    CHECK (restored_at >= started_at)
);
CREATE INDEX IF NOT EXISTS ix_fact_incident_service_started
    ON core.fact_incident(service_key, started_at);

-- This view describes only the fictional bank's simulated incidents.
CREATE OR REPLACE VIEW mart.service_incident_summary AS
SELECT s.service_id, s.service_name, s.impact_tolerance_minutes,
       count(i.incident_id) AS incident_count,
       count(i.incident_id) FILTER
         (WHERE i.duration_minutes > s.impact_tolerance_minutes) AS tolerance_breach_count,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY i.duration_minutes)
         AS median_duration_minutes,
       sum(i.customers_affected) AS customers_affected_sum,
       sum(i.loss_gbp) AS incident_loss_gbp_sum
FROM core.dim_service s
LEFT JOIN core.fact_incident i ON i.service_key = s.service_key
GROUP BY s.service_key, s.service_id, s.service_name, s.impact_tolerance_minutes;
COMMIT;
