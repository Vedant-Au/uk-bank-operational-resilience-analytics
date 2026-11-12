"""Recovery gaps by service and supplier concentration for the fictional bank.

Two questions a resilience committee can act on:

1. Recovery gap: how much faster would each service have to restore service to
   cut its simulated impact-tolerance breaches by half, or clear them all?
2. Supplier concentration: if one supplier went fully down, which services would
   it take past tolerance, and how quickly?

Everything here runs on the simulated internal layer only. Standard library only.
"""

import argparse
import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "04_etl"))
from generate_simulated_bank import SEED, SERVICES, SUPPLIERS, generate, validate

CUTS = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]          # % shorter recovery
OUTAGES = [30, 60, 90, 120, 180, 240, 360, 480]         # supplier outage minutes
TOLERANCE = {s[0]: s[2] for s in SERVICES}
SERVICE_NAME = {s[0]: s[1] for s in SERVICES}
SERVICE_SCALE = {s[0]: s[4] for s in SERVICES}           # illustrative customer base
SUPPLIER_INFO = {p[0]: p for p in SUPPLIERS}


def duration_minutes(row):
    start = datetime.fromisoformat(row["started_at"])
    end = datetime.fromisoformat(row["restored_at"])
    return (end - start).total_seconds() / 60


def required_cut(duration, tolerance):
    """Smallest % reduction in duration that brings this episode within tolerance."""
    if duration <= tolerance:
        return 0.0
    return (1 - tolerance / duration) * 100


def cut_to_clear(cuts_needed, share):
    """% cut that clears at least `share` of the breaches (0 < share <= 1)."""
    if not cuts_needed:
        return 0.0
    ordered = sorted(cuts_needed)
    k = math.ceil(share * len(ordered))
    return ordered[k - 1]


def ceil1(value):
    """Round up to one decimal so a reported cut is always enough."""
    return math.ceil(value * 10 - 1e-9) / 10


def recovery_gap(incidents):
    """Per-service summary and breach curve for one generated world."""
    by_service = {sid: [] for sid in TOLERANCE}
    for row in incidents:
        by_service[row["service_id"]].append(duration_minutes(row))
    summary, curve = {}, {}
    for sid, durations in by_service.items():
        tol = TOLERANCE[sid]
        breaches = [d for d in durations if d > tol]
        cuts_needed = [required_cut(d, tol) for d in breaches]
        summary[sid] = {
            "episodes": len(durations),
            "breaches": len(breaches),
            "median_minutes": statistics.median(durations) if durations else None,
            "longest_minutes": max(durations) if durations else None,
            "minutes_beyond_tolerance": round(sum(d - tol for d in breaches)),
            "cut_to_halve_breaches_pct": ceil1(cut_to_clear(cuts_needed, .5)),
            "cut_to_clear_all_pct": ceil1(cut_to_clear(cuts_needed, 1)),
        }
        curve[sid] = [sum(d * (1 - c / 100) > tol for d in durations) for c in CUTS]
    return summary, curve


def supplier_exposure():
    """Structural stress test: full outage of one supplier, no failover assumed."""
    rows, stress = [], []
    for pid, name, kind, substitutability in SUPPLIERS:
        dependants = [s for s in SERVICES if pid in s[5]]
        tolerances = sorted(s[2] for s in dependants)
        rows.append({
            "supplier_id": pid, "supplier_name": name, "supplier_type": kind,
            "substitutability": substitutability,
            "services_supported": len(dependants),
            "service_names": "; ".join(s[1] for s in dependants),
            "high_criticality_services": sum(s[3] == "high" for s in dependants),
            "minutes_to_first_breach": tolerances[0],
            "minutes_to_breach_all": tolerances[-1],
            "illustrative_customer_base": sum(s[4] for s in dependants),
        })
        for minutes in OUTAGES:
            hit = [s for s in dependants if minutes > s[2]]
            stress.append({
                "supplier_id": pid, "supplier_name": name, "outage_minutes": minutes,
                "services_beyond_tolerance": len(hit),
                "services_hit": "; ".join(s[1] for s in hit),
                "illustrative_customers_beyond_tolerance": sum(s[4] for s in hit),
            })
    return rows, stress


def shared_event_counts(incidents):
    events = {}
    for row in incidents:
        if row["shared_event_id"]:
            events.setdefault(row["supplier_id"], set()).add(row["shared_event_id"])
    return {pid: len(ids) for pid, ids in events.items()}


def analyse(default_data, seed_start=SEED, runs=50):
    if errors := validate(default_data):
        raise ValueError("Invalid default run: " + "; ".join(errors))
    default_summary, default_curve = recovery_gap(default_data["incidents"])

    seed_halve = {sid: [] for sid in TOLERANCE}
    seed_all = {sid: [] for sid in TOLERANCE}
    seed_curve = {sid: [[] for _ in CUTS] for sid in TOLERANCE}
    seed_events = {pid: [] for pid in SUPPLIER_INFO}
    for seed in range(seed_start, seed_start + runs):
        incidents = generate(seed)["incidents"]
        summary, curve = recovery_gap(incidents)
        for sid in TOLERANCE:
            if summary[sid]["breaches"]:
                seed_halve[sid].append(summary[sid]["cut_to_halve_breaches_pct"])
                seed_all[sid].append(summary[sid]["cut_to_clear_all_pct"])
            for i, value in enumerate(curve[sid]):
                seed_curve[sid][i].append(value)
        counts = shared_event_counts(incidents)
        for pid in SUPPLIER_INFO:
            seed_events[pid].append(counts.get(pid, 0))

    def med(values):
        return round(statistics.median(values), 1) if values else None

    services = []
    for sid in TOLERANCE:
        services.append({
            "service_id": sid, "service_name": SERVICE_NAME[sid],
            "impact_tolerance_minutes": TOLERANCE[sid],
            **default_summary[sid],
            "seeds_with_breaches": len(seed_halve[sid]),
            "seed_median_cut_to_halve_pct": med(seed_halve[sid]),
            "seed_median_cut_to_clear_all_pct": med(seed_all[sid]),
        })
    curve_rows = []
    for sid in TOLERANCE:
        for i, cut in enumerate(CUTS):
            curve_rows.append({
                "service_id": sid, "service_name": SERVICE_NAME[sid],
                "recovery_cut_pct": cut,
                "default_seed_breaches": default_curve[sid][i],
                "seed_median_breaches": med(seed_curve[sid][i]),
            })
    exposure, stress = supplier_exposure()
    default_events = shared_event_counts(default_data["incidents"])
    for row in exposure:
        pid = row["supplier_id"]
        row["default_seed_shared_events"] = default_events.get(pid, 0)
        row["seed_median_shared_events"] = med(seed_events[pid])
    return {
        "provenance": "simulated_internal_sensitivity_only",
        "default_seed": SEED, "sensitivity_seeds": [seed_start, seed_start + runs - 1],
        "assumptions": ("Recovery cut applies to every episode of a service. Supplier stress "
                        "assumes a full outage of the supplier stops each dependent service for "
                        "the outage duration, with no failover. Customer base is the "
                        "generator's illustrative scale, not an estimate."),
        "service_recovery_gap": services,
        "recovery_curve": curve_rows,
        "supplier_exposure": exposure,
        "supplier_outage_stress": stress,
        "real_bank_probability_estimated": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("02_data/processed/resilience_gaps.json"))
    parser.add_argument("--runs", type=int, default=50)
    args = parser.parse_args()
    result = analyse(generate(SEED), runs=args.runs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for s in result["service_recovery_gap"]:
        print(f"{s['service_name']:<22} breaches {s['breaches']:>2}/{s['episodes']:<2} "
              f"halve: {s['cut_to_halve_breaches_pct']:>5}% (seed median {s['seed_median_cut_to_halve_pct']}) "
              f"clear all: {s['cut_to_clear_all_pct']:>5}% (seed median {s['seed_median_cut_to_clear_all_pct']})")
    for e in result["supplier_exposure"]:
        print(f"{e['supplier_name']:<17} services {e['services_supported']} first breach {e['minutes_to_first_breach']} min, "
              f"all {e['minutes_to_breach_all']} min, customers {e['illustrative_customer_base']}, "
              f"shared events default {e['default_seed_shared_events']} / seed median {e['seed_median_shared_events']}")
    print(f"Saved {args.output}")
