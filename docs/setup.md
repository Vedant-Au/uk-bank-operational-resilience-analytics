# Setup

Built and tested on macOS (Apple silicon) with Anaconda Python 3 and PostgreSQL 18 via Postgres.app.

## Python only (no database)

The simulation, scenario comparison, recovery-gap analysis, dashboard data and Excel dashboard need only Python 3.10+ and `openpyxl`:

```bash
pip install -r requirements.txt
bash run_pipeline.sh
```

## PostgreSQL warehouse (optional, for the SQL layer)

1. Install **Postgres.app** with PostgreSQL 18 from https://postgresapp.com/downloads.html, open it and click **Initialize**.
2. From the project root:

```bash
PSQL=/Applications/Postgres.app/Contents/Versions/latest/bin
$PSQL/createdb risk_analytics
$PSQL/psql -d risk_analytics -v ON_ERROR_STOP=1 -f 03_sql/001_foundation.sql
$PSQL/psql -d risk_analytics -v ON_ERROR_STOP=1 -f 03_sql/002_smoke_test.sql
$PSQL/psql -d risk_analytics -v ON_ERROR_STOP=1 -f 03_sql/003_open_banking.sql
```

3. Load the data (the loaders use `psycopg`; set `RISK_DATABASE_URL` in your environment, never in a committed file):

```bash
python3 04_etl/ingest_open_banking.py "path/to/Historic Data Download.csv"      # optional public panel
python3 04_etl/generate_simulated_bank.py
python3 04_etl/load_simulated_bank.py 02_data/simulated_internal
$PSQL/psql -d risk_analytics -v ON_ERROR_STOP=1 -f 03_sql/004_open_banking_quality.sql
$PSQL/psql -d risk_analytics -v ON_ERROR_STOP=1 -f 03_sql/005_open_banking_eda.sql
$PSQL/psql -P pager=off -d risk_analytics -v ON_ERROR_STOP=1 -f 03_sql/006_simulated_quality.sql
```

The loader refuses a second run with a different manifest in the same database; repeating the same run is a no-op.
