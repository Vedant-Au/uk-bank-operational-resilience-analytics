"""Generate and validate a fictional bank dataset. Standard library only."""

import argparse
import csv
import hashlib
import json
import math
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

VERSION = "1.0"
SEED = 280926
SERVICES = [
    ("S01", "Everyday payments", 120, "high", 42000, ["P01", "P02"]),
    ("S02", "Mobile account access", 180, "high", 68000, ["P01", "P03"]),
    ("S03", "Card authorisation", 90, "high", 55000, ["P02", "P04"]),
    ("S04", "Mortgage servicing", 480, "medium", 9000, ["P03", "P05"]),
]
SUPPLIERS = [
    ("P01", "Provider Alpha", "cloud platform", "low"),
    ("P02", "Provider Beta", "payment processing", "low"),
    ("P03", "Provider Gamma", "identity platform", "medium"),
    ("P04", "Provider Delta", "card network", "medium"),
    ("P05", "Provider Epsilon", "document service", "high"),
]


def months():
    year, month = 2024, 9
    for _ in range(24):
        yield date(year, month, 1)
        year += month // 12
        month = month % 12 + 1


def generate(seed=SEED):
    rng = random.Random(seed)
    services = [{"service_id": sid, "service_name": name,
                 "impact_tolerance_minutes": tol, "criticality": crit}
                for sid, name, tol, crit, _, _ in SERVICES]
    suppliers = [{"supplier_id": sid, "supplier_name": name, "supplier_type": typ,
                  "substitutability": sub} for sid, name, typ, sub in SUPPLIERS]
    dependencies = [{"service_id": sid, "supplier_id": pid, "valid_from": "2024-09-01"}
                    for sid, _, _, _, _, deps in SERVICES for pid in deps]
    observations, incidents = [], []
    event_number = 0

    def incident(service, month, event_id, supplier_id=None):
        nonlocal event_number
        event_number += 1
        sid, _, tolerance, _, scale, _ = service
        day = rng.randrange(1, 25)
        hour, minute = rng.randrange(24), rng.randrange(60)
        start = datetime(month.year, month.month, day, hour, minute, tzinfo=timezone.utc)
        duration = max(10, min(900, round(rng.lognormvariate(math.log(95), .72))))
        detection = min(duration, round(duration * rng.uniform(.05, .35)))
        return {"incident_id": f"I{event_number:04d}", "shared_event_id": event_id or "",
                "service_id": sid, "supplier_id": supplier_id or "",
                "started_at": start.isoformat(),
                "detected_at": (start + timedelta(minutes=detection)).isoformat(),
                "restored_at": (start + timedelta(minutes=duration)).isoformat(),
                "incident_type": "shared_supplier_scenario" if event_id else "local_service_scenario",
                "severity": "high" if duration > tolerance else "medium" if duration >= 60 else "low",
                "customers_affected": str(round(scale * rng.uniform(.02, .25))),
                "loss_gbp": f"{duration * rng.uniform(8, 65):.2f}"}

    for month in months():
        for pid, *_ in SUPPLIERS:
            observations.append({"supplier_id": pid, "observation_date": month.isoformat(),
                                 "availability_pct": f"{rng.uniform(98, 100):.3f}",
                                 "warning_indicator": str(rng.random() < .12).lower()})
        for _ in range(rng.randrange(4)):
            incidents.append(incident(rng.choice(SERVICES), month, None))
        if rng.random() < .16:
            pid = rng.choice(["P01", "P02", "P03"])
            linked = [s for s in SERVICES if pid in s[5]]
            event_id = f"E{month:%Y%m}-{pid}"
            incidents.extend(incident(s, month, event_id, pid) for s in linked)
    return {"services": services, "suppliers": suppliers, "dependencies": dependencies,
            "supplier_observations": observations, "incidents": incidents}


def validate(data):
    errors = []
    ids = {s["service_id"] for s in data["services"]}
    supplier_ids = {s["supplier_id"] for s in data["suppliers"]}
    deps = {(d["service_id"], d["supplier_id"]) for d in data["dependencies"]}
    incident_ids = [i["incident_id"] for i in data["incidents"]]
    if len(incident_ids) != len(set(incident_ids)):
        errors.append("duplicate incident ID")
    for i in data["incidents"]:
        if i["service_id"] not in ids or (i["supplier_id"] and
            (i["supplier_id"] not in supplier_ids or
             (i["service_id"], i["supplier_id"]) not in deps)):
            errors.append(f"{i['incident_id']}: invalid service or supplier dependency")
        start, detection, end = (datetime.fromisoformat(i[k]) for k in
                                 ("started_at", "detected_at", "restored_at"))
        if not start <= detection <= end or start == end:
            errors.append(f"{i['incident_id']}: invalid event timestamps")
        if i["supplier_id"] and not i["shared_event_id"]:
            errors.append(f"{i['incident_id']}: supplier event requires shared event ID")
    groups = {}
    for i in data["incidents"]:
        if i["shared_event_id"]:
            groups.setdefault(i["shared_event_id"], []).append(i)
    for event_id, rows in groups.items():
        if len(rows) < 2 or len({r["supplier_id"] for r in rows}) != 1 or len({r["service_id"] for r in rows}) != len(rows):
            errors.append(f"{event_id}: invalid shared event grouping")
    expected_dates = {m.isoformat() for m in months()}
    observed = {(r["supplier_id"], r["observation_date"]) for r in data["supplier_observations"]}
    if observed != {(pid, d) for pid in supplier_ids for d in expected_dates} or len(observed) != len(data["supplier_observations"]):
        errors.append("supplier observation calendar incomplete or duplicated")
    for r in data["supplier_observations"]:
        if not 0 <= float(r["availability_pct"]) <= 100:
            errors.append("supplier availability outside 0–100")
    return errors


def write(destination: Path, seed=SEED):
    data = generate(seed)
    errors = validate(data)
    if errors:
        raise ValueError("; ".join(errors))
    destination.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, rows in data.items():
        path = destination / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        files[name] = {"rows": len(rows), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    manifest = {"generator_version": VERSION, "seed": seed,
                "provenance": "simulated_internal", "period": ["2024-09", "2026-08"],
                "source_public_data_used": False, "files": files,
                "assumptions": "02_data/simulation_design.md"}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("02_data/simulated_internal"))
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    print(json.dumps(write(args.output, args.seed), indent=2))
