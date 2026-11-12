# Data folders

Four working folders sit under `02_data/`. They are created on your machine when you run the scripts and are kept out of Git:

| Folder | What goes in it | Created by |
|---|---|---|
| `raw/`, `external/` | The Open Banking historical CSV, downloaded from https://www.openbanking.org.uk/api-performance/ (not redistributed here; see the licence note in `data_source_register.md`) | You |
| `simulated_internal/` | The seeded fictional bank: services, suppliers, dependencies, incidents, supplier observations and a manifest with checksums | `04_etl/generate_simulated_bank.py` |
| `processed/` | Scenario and recovery-gap results (JSON), the local public monthly panel and the Excel dashboard with public context | `05_modelling/*.py`, `08_dashboard/*.py` |

The simulated data that the dashboard uses is committed in `08_dashboard/data/`, so you can open the Excel dashboard without running anything.
