"""Validate the publisher's metric-by-month CSV and load it into PostgreSQL.

Run --validate-only without dependencies. Loading requires psycopg 3.
Public aggregate data stays in the public staging layer, separate from simulated data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

SOURCE_URL = "https://www.openbanking.org.uk/api-performance/"


def read_and_validate(path: Path) -> tuple[list[str], list[tuple[str, str, str, str]], list[tuple[int, dict[str, str]]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2 or rows[0][0] != "Values":
        raise ValueError("Expected a Values column and monthly YYYYMM headers")
    header = rows[0]
    months = header[1:]
    if len(months) < 2 or len(months) != len(set(months)):
        raise ValueError("At least two unique months are required")
    dates = []
    for month in months:
        if len(month) != 6 or not month.isdigit():
            raise ValueError(f"Invalid month header: {month!r}")
        dates.append(datetime.strptime(month, "%Y%m").date().replace(day=1))
    if dates != sorted(dates):
        raise ValueError("Months are not chronological")
    for previous, current in zip(dates, dates[1:]):
        if (current.year - previous.year) * 12 + current.month - previous.month != 1:
            raise ValueError(f"Missing month between {previous} and {current}")

    measures: list[tuple[str, str, str, str]] = []
    source_rows: list[tuple[int, dict[str, str]]] = []
    seen_metrics: set[str] = set()
    parsed: dict[str, dict[str, float]] = {}
    for row_no, row in enumerate(rows[1:], start=1):
        if len(row) != len(header):
            raise ValueError(f"Row {row_no} has {len(row)} rather than {len(header)} columns")
        name = row[0].strip()
        if not name or name in seen_metrics:
            raise ValueError(f"Missing or duplicate metric at row {row_no}: {name!r}")
        seen_metrics.add(name)
        source_rows.append((row_no, dict(zip(header, row))))
        parsed[name] = {}
        unit = "percent" if name.startswith("%") or "Availability %" in name else (
            "milliseconds" if name == "API Response Time" else "count"
        )
        for month, original in zip(months, row[1:]):
            value = original.strip().replace(",", "")
            if unit == "percent":
                if not value.endswith("%"):
                    raise ValueError(f"Expected percent symbol in {name}, {month}")
                value = value[:-1]
            if not value:
                raise ValueError(f"Blank value in {name}, {month}")
            try:
                number = float(value)
            except ValueError as exc:
                raise ValueError(f"Invalid number in {name}, {month}: {original!r}") from exc
            if not 0 <= number <= (100 if unit == "percent" else float("inf")):
                raise ValueError(f"Out-of-range value in {name}, {month}")
            if unit == "count" and not number.is_integer():
                raise ValueError(f"Noninteger count in {name}, {month}")
            parsed[name][month] = number
            measures.append((month + "01", name, unit, value))

    failures = parsed.get("# of API Calls Failed")
    business = parsed.get("# of API Calls failed for Business Reasons")
    technical = parsed.get("# of API Calls failed for Technical Reasons")
    if failures is None or business is None or technical is None:
        raise ValueError("Required failure categories missing")
    for month in months:
        if failures[month] != business[month] + technical[month]:
            raise ValueError(f"Failure categories do not reconcile in {month}")
    return months, measures, source_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--dbname", default="risk_analytics")
    args = parser.parse_args()
    months, measures, source_rows = read_and_validate(args.csv_file)
    sha256 = hashlib.sha256(args.csv_file.read_bytes()).hexdigest()
    print(json.dumps({"source_sha256": sha256, "metrics": len(source_rows),
                      "months": len(months), "observations": len(measures),
                      "coverage": [months[0], months[-1]]}))
    if args.validate_only:
        return

    try:
        import psycopg
        from psycopg.types.json import Jsonb
    except ImportError as exc:
        raise SystemExit("Install psycopg 3 first: python -m pip install 'psycopg[binary]'") from exc

    with psycopg.connect(dbname=args.dbname) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT batch_id FROM raw.source_batch WHERE sha256 = %s AND source_name = %s",
                        (sha256, "Open Banking API performance"))
            if prior := cur.fetchone():
                print(f"Already loaded as batch {prior[0]}; no duplicate inserted")
                return
            cur.execute("""INSERT INTO raw.source_batch
                        (source_name,source_kind,source_url,source_file,sha256,
                         coverage_start,coverage_end,license_note)
                        VALUES (%s,'public',%s,%s,%s,%s,%s,%s) RETURNING batch_id""",
                        ("Open Banking API performance", SOURCE_URL, args.csv_file.name,
                         sha256, months[0] + "01", months[-1] + "01",
                         "Publisher reuse terms to verify before redistribution"))
            batch_id = cur.fetchone()[0]
            cur.executemany("INSERT INTO raw.source_row(batch_id,row_number,payload) VALUES (%s,%s,%s)",
                            [(batch_id, n, Jsonb(payload)) for n, payload in source_rows])
            cur.executemany("""INSERT INTO stg.open_banking_metric
                        (batch_id,observation_month,metric_name,unit,metric_value)
                        VALUES (%s,%s,%s,%s,%s)""",
                        [(batch_id, month, name, unit, value) for month, name, unit, value in measures])
        # psycopg transaction commits only after all source and staging inserts succeed.
    print(f"Loaded batch {batch_id}: {len(source_rows)} raw rows; {len(measures)} typed observations")


if __name__ == "__main__":
    main()
