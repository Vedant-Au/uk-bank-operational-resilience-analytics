"""Paired toy scenario comparison across explicit seeds and effects."""

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "04_etl"))
from generate_simulated_bank import SERVICES, SEED, generate, validate
from load_simulated_bank import read_run

OPTIONS = {
    "card_recovery": lambda row: row["service_id"] == "S03",
    "payments_recovery": lambda row: row["service_id"] == "S01",
    "shared_provider_coordination": lambda row: bool(row["shared_event_id"]),
}
EFFECTS = {"optimistic": .50, "central": .70, "cautious": .90}
TOLERANCE = {s[0]: s[2] for s in SERVICES}


def breach_count(incidents, option=None, multiplier=1.0):
    if not 0 <= multiplier <= 1:
        raise ValueError("Duration multiplier must be between 0 and 1")
    total = 0
    for row in incidents:
        duration = (datetime.fromisoformat(row["restored_at"]) -
                    datetime.fromisoformat(row["started_at"])).total_seconds() / 60
        if option and OPTIONS[option](row):
            duration *= multiplier
        total += duration > TOLERANCE[row["service_id"]]
    return total


def compare(default_data, seed_start=SEED, runs=50):
    if runs < 2 or runs > 1000:
        raise ValueError("Choose between 2 and 1000 synthetic seeds")
    if errors := validate(default_data):
        raise ValueError("Invalid default run: " + "; ".join(errors))
    default_rows = default_data["incidents"]
    default_baseline = breach_count(default_rows)
    default_result = {name: {effect: default_baseline - breach_count(default_rows, name, multiplier)
                             for effect, multiplier in EFFECTS.items()} for name in OPTIONS}
    samples = {name: {effect: [] for effect in EFFECTS} for name in OPTIONS}
    baseline_samples = []
    for seed in range(seed_start, seed_start + runs):
        rows = generate(seed)["incidents"]
        baseline = breach_count(rows)
        baseline_samples.append(baseline)
        for name in OPTIONS:
            for effect, multiplier in EFFECTS.items():
                avoided = baseline - breach_count(rows, name, multiplier)
                assert 0 <= avoided <= baseline
                samples[name][effect].append(avoided)
    return {
        "provenance": "simulated_internal_sensitivity_only",
        "assumptions_file": "05_modelling/scenario_assumptions.md",
        "default_seed": SEED, "default_baseline_breaches": default_baseline,
        "default_incident_impact_rows": len(default_rows),
        "default_avoided_breaches": default_result,
        "sensitivity_seeds": [seed_start, seed_start + runs - 1],
        "baseline_breaches_across_synthetic_seeds": {
            "min": min(baseline_samples), "median": statistics.median(baseline_samples),
            "max": max(baseline_samples)},
        "avoided_breaches_across_synthetic_seeds": {
            name: {effect: {"min": min(values), "median": statistics.median(values),
                            "max": max(values), "zero_effect_runs": values.count(0)}
                   for effect, values in effects.items()}
            for name, effects in samples.items()},
        "status": "illustrative_only_human_exercise_validation_required",
        "real_bank_probability_estimated": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("02_data/simulated_internal"))
    parser.add_argument("--output", type=Path, default=Path("02_data/processed/scenario_comparison.json"))
    parser.add_argument("--runs", type=int, default=50)
    args = parser.parse_args()
    manifest, data = read_run(args.directory)
    if manifest["seed"] != SEED:
        raise ValueError("Use default-seed source run; sensitivity seeds are generated separately")
    result = compare(data, runs=args.runs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {args.output}: default baseline {result['default_baseline_breaches']} simulated breaches; {args.runs} synthetic seeds")
