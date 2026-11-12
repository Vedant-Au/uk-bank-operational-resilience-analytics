"""Validate generated files, then load one fictional bank run atomically."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from generate_simulated_bank import validate

SOURCE_NAME = "Fictional bank simulation v1"


def read_run(directory: Path):
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("generator_version") != "1.0" or manifest.get("provenance") != "simulated_internal" or manifest.get("source_public_data_used") is not False:
        raise ValueError("Invalid simulation provenance or generator version")
    data = {}
    for name, recorded in manifest["files"].items():
        path = directory / f"{name}.csv"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != recorded["sha256"]:
            raise ValueError(f"Checksum mismatch: {path}")
        with path.open(newline="", encoding="utf-8") as handle:
            data[name] = list(csv.DictReader(handle))
        if len(data[name]) != recorded["rows"]:
            raise ValueError(f"Row count mismatch: {path}")
    if set(data) != {"services", "suppliers", "dependencies", "supplier_observations", "incidents"}:
        raise ValueError("Missing or unexpected simulation table")
    errors = validate(data)
    if errors:
        raise ValueError("; ".join(errors))
    return manifest, data


def load(directory: Path, dbname: str):
    manifest, data = read_run(directory)
    try:
        import psycopg
        from psycopg.types.json import Jsonb
    except ImportError as exc:
        raise SystemExit("Activate the riskanalytics Conda environment with psycopg installed") from exc
    sha = hashlib.sha256((directory / "manifest.json").read_bytes()).hexdigest()
    with psycopg.connect(dbname=dbname) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT batch_id, sha256 FROM raw.source_batch WHERE source_kind='simulated_internal' ORDER BY batch_id")
            prior = cur.fetchall()
            if prior:
                if len(prior) == 1 and prior[0][1] == sha:
                    print(f"Already loaded as batch {prior[0][0]}; no duplicate inserted")
                    return
                raise ValueError("Different simulation already loaded. Preserve it; use a fresh database for another seed")
            cur.execute("""INSERT INTO raw.source_batch
                        (source_name,source_kind,source_file,sha256,coverage_start,coverage_end,license_note)
                        VALUES (%s,'simulated_internal',%s,%s,%s,%s,%s) RETURNING batch_id""",
                        (SOURCE_NAME, "manifest.json", sha, "2024-09-01", "2026-08-31",
                         f"Fictional simulated data; generator v{manifest['generator_version']}; seed {manifest['seed']}"))
            batch = cur.fetchone()[0]
            n = 0
            for table, rows in data.items():
                for row in rows:
                    n += 1
                    cur.execute("INSERT INTO raw.source_row(batch_id,row_number,payload) VALUES (%s,%s,%s)",
                                (batch, n, Jsonb({"entity": table, **row})))
            cur.executemany("""INSERT INTO stg.service
                        (service_id,service_name,impact_tolerance_minutes,criticality,batch_id)
                        VALUES (%s,%s,%s,%s,%s)""",
                        [(r["service_id"], r["service_name"], r["impact_tolerance_minutes"], r["criticality"], batch)
                         for r in data["services"]])
            cur.executemany("""INSERT INTO stg.supplier
                        (supplier_id,supplier_name,supplier_type,substitutability,batch_id)
                        VALUES (%s,%s,%s,%s,%s)""",
                        [(r["supplier_id"], r["supplier_name"], r["supplier_type"], r["substitutability"], batch)
                         for r in data["suppliers"]])
            cur.executemany("""INSERT INTO stg.service_supplier(service_id,supplier_id,valid_from)
                        VALUES (%s,%s,%s)""",
                        [(r["service_id"], r["supplier_id"], r["valid_from"]) for r in data["dependencies"]])
            cur.executemany("""INSERT INTO stg.supplier_observation
                        (supplier_id,observation_date,availability_pct,warning_indicator,batch_id)
                        VALUES (%s,%s,%s,%s,%s)""",
                        [(r["supplier_id"], r["observation_date"], r["availability_pct"],
                          r["warning_indicator"] == "true", batch) for r in data["supplier_observations"]])
            cur.executemany("""INSERT INTO stg.incident
                        (incident_id,shared_event_id,service_id,supplier_id,started_at,detected_at,
                         restored_at,incident_type,severity,customers_affected,loss_gbp,batch_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                        [(r["incident_id"], r["shared_event_id"] or None, r["service_id"],
                          r["supplier_id"] or None, r["started_at"], r["detected_at"],
                          r["restored_at"], r["incident_type"], r["severity"],
                          r["customers_affected"], r["loss_gbp"], batch) for r in data["incidents"]])
            cur.execute("""INSERT INTO core.dim_service(service_id,service_name,impact_tolerance_minutes)
                        SELECT service_id,service_name,impact_tolerance_minutes FROM stg.service WHERE batch_id=%s""", (batch,))
            cur.execute("""INSERT INTO core.dim_supplier(supplier_id,supplier_name,supplier_type)
                        SELECT supplier_id,supplier_name,supplier_type FROM stg.supplier WHERE batch_id=%s""", (batch,))
            cur.execute("""INSERT INTO core.fact_incident
                        (incident_id,shared_event_id,service_key,supplier_key,started_at,restored_at,
                         customers_affected,loss_gbp,batch_id)
                        SELECT i.incident_id,i.shared_event_id,s.service_key,p.supplier_key,
                               i.started_at,i.restored_at,i.customers_affected,i.loss_gbp,i.batch_id
                        FROM stg.incident i JOIN core.dim_service s ON s.service_id=i.service_id
                        LEFT JOIN core.dim_supplier p ON p.supplier_id=i.supplier_id
                        WHERE i.batch_id=%s""", (batch,))
    print(f"Loaded simulated batch {batch}: {n} raw rows; {len(data['incidents'])} incident-impact rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--dbname", default="risk_analytics")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    if args.validate_only:
        manifest, data = read_run(args.directory)
        print(json.dumps({"status": "valid", "seed": manifest["seed"],
                          "rows": {name: len(rows) for name, rows in data.items()}}))
    else:
        load(args.directory, args.dbname)
