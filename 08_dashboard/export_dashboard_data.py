"""Export the dashboard data sources (Excel and Tableau) from the simulated layer.

Writes simulated-only CSVs to 08_dashboard/data/. These are invented records
and safe to publish. The public Open Banking monthly panel is optional and is
written to 02_data/processed/ (excluded from Git) because the publisher has not
granted an open licence for redistribution.

    python3 08_dashboard/export_dashboard_data.py
    python3 08_dashboard/export_dashboard_data.py --open-banking-csv "path/to/Historic Data Download.csv"
"""

import argparse
import csv
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "04_etl"))
sys.path.insert(0, str(ROOT / "05_modelling"))
from generate_simulated_bank import SEED, SERVICES, SUPPLIERS, generate, validate
from compare_exercises import EFFECTS, compare
from resilience_gaps import TOLERANCE, analyse, duration_minutes

LABELS = {"card_recovery": "Card recovery rehearsal",
          "payments_recovery": "Payments recovery rehearsal",
          "shared_provider_coordination": "Shared-provider coordination"}


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {path.relative_to(ROOT)}  ({len(rows)} rows)")


def service_rows(data):
    rows = []
    for sid, name, tol, crit, scale, deps in SERVICES:
        inc = [r for r in data["incidents"] if r["service_id"] == sid]
        durations = [duration_minutes(r) for r in inc]
        rows.append({
            "source_kind": "simulated_internal", "service_id": sid, "service_name": name,
            "criticality": crit, "impact_tolerance_minutes": tol,
            "incident_count": len(inc),
            "tolerance_breach_count": sum(d > tol for d in durations),
            "median_duration_minutes": statistics.median(durations),
            "customers_affected_sum": sum(int(r["customers_affected"]) for r in inc),
            "incident_loss_gbp_sum": round(sum(float(r["loss_gbp"]) for r in inc), 2),
        })
    return rows


def incident_rows(data):
    names = {s[0]: s[1] for s in SERVICES}
    suppliers = {p[0]: p[1] for p in SUPPLIERS}
    rows = []
    for r in data["incidents"]:
        minutes = round(duration_minutes(r))
        tol = TOLERANCE[r["service_id"]]
        rows.append({
            "source_kind": "simulated_internal", "incident_id": r["incident_id"],
            "shared_event_id": r["shared_event_id"], "service_id": r["service_id"],
            "service_name": names[r["service_id"]],
            "supplier_name": suppliers.get(r["supplier_id"], ""),
            "incident_type": r["incident_type"], "start_month": r["started_at"][:7] + "-01",
            "duration_minutes": minutes, "impact_tolerance_minutes": tol,
            "beyond_tolerance": int(minutes > tol), "minutes_beyond_tolerance": max(0, minutes - tol),
            "customers_affected": int(r["customers_affected"]), "loss_gbp": float(r["loss_gbp"]),
        })
    return rows


def dependency_rows():
    suppliers = {p[0]: p for p in SUPPLIERS}
    return [{"source_kind": "simulated_internal", "service_id": sid, "service_name": name,
             "criticality": crit, "impact_tolerance_minutes": tol,
             "supplier_id": pid, "supplier_name": suppliers[pid][1],
             "supplier_type": suppliers[pid][2], "substitutability": suppliers[pid][3]}
            for sid, name, tol, crit, _, deps in SERVICES for pid in deps]


def scenario_rows(result):
    rows = []
    for option, effects in result["avoided_breaches_across_synthetic_seeds"].items():
        for effect, stats in effects.items():
            rows.append({
                "source_kind": "simulated_internal_sensitivity_only", "option": option,
                "option_label": LABELS[option], "effect_case": effect,
                "duration_multiplier": EFFECTS[effect],
                "default_baseline_breaches": result["default_baseline_breaches"],
                "default_avoided_breaches": result["default_avoided_breaches"][option][effect],
                "avoided_min": stats["min"], "avoided_median": stats["median"],
                "avoided_max": stats["max"], "zero_effect_runs": stats["zero_effect_runs"],
                "synthetic_seed_count": result["sensitivity_seeds"][1] - result["sensitivity_seeds"][0] + 1,
            })
    return rows


def tagged(rows, kind="simulated_internal"):
    return [{"source_kind": kind, **row} for row in rows]


def public_rows(path):
    from ingest_open_banking import read_and_validate
    _, measures, _ = read_and_validate(path)
    wanted = {"# of API Calls Successful": "successful_calls",
              "# of API Calls Failed": "failed_calls",
              "# of API Calls failed for Technical Reasons": "technical_failures",
              "Availability %": "availability_pct",
              "Availability % - Weighted": "weighted_availability_pct",
              "API Response Time": "response_time_ms"}
    table = {}
    for month, name, _, value in measures:
        if name in wanted:
            iso = f"{month[:4]}-{month[4:6]}-01"
            table.setdefault(iso, {})[wanted[name]] = float(value)
    return [{"source_kind": "public_aggregate", "observation_month": m,
             **{c: table[m].get(c) for c in wanted.values()}} for m in sorted(table)]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open-banking-csv", type=Path)
    args = parser.parse_args()
    data = generate(SEED)
    if errors := validate(data):
        raise SystemExit("; ".join(errors))
    gaps = analyse(data)
    out = ROOT / "08_dashboard" / "data"
    print("Simulated dashboard sources:")
    write_csv(out / "services.csv", service_rows(data))
    write_csv(out / "incidents.csv", incident_rows(data))
    write_csv(out / "dependencies.csv", dependency_rows())
    write_csv(out / "scenarios.csv", scenario_rows(compare(data)))
    write_csv(out / "recovery_gap.csv", tagged(gaps["service_recovery_gap"]))
    write_csv(out / "recovery_curve.csv", tagged(gaps["recovery_curve"]))
    write_csv(out / "supplier_exposure.csv", tagged(gaps["supplier_exposure"]))
    write_csv(out / "supplier_outage_stress.csv", tagged(gaps["supplier_outage_stress"]))
    if args.open_banking_csv:
        print("Public context (local only, not committed):")
        write_csv(ROOT / "02_data" / "processed" / "public_monthly.csv", public_rows(args.open_banking_csv))
