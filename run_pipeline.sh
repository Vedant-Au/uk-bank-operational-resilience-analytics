#!/usr/bin/env bash
# Rebuild everything that does not need the database, then run the tests.
set -euo pipefail
cd "$(dirname "$0")"
python3 04_etl/generate_simulated_bank.py > /dev/null
python3 04_etl/load_simulated_bank.py 02_data/simulated_internal --validate-only
python3 05_modelling/compare_exercises.py
python3 05_modelling/resilience_gaps.py
python3 08_dashboard/export_dashboard_data.py
python3 08_dashboard/build_excel_dashboard.py
python3 -m unittest discover -s 05_modelling -p 'test_*.py'
