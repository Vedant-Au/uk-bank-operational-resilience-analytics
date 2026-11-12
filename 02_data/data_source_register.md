# Public source register

First checked 2026-09-28; licence position re-checked 2026-11-12. Before acquisition record the exact downloaded file, version/update date, retrieval timestamp, checksum, reuse terms, data dictionary, coverage and known breaks. Sources remain separate from fictional-bank records.

| Candidate | Granularity and intended use | Principal limitation | Decision |
| --- | --- | --- | --- |
| [FCA operational resilience guidance](https://www.fca.org.uk/firms/operational-resilience), [SYSC 15A](https://handbook.fca.org.uk/handbook/SYSC/15A/) | Requirements and terminology, not numerical input | Does not provide bank incident rates or universal impact tolerances | Use as framing |
| [Open Banking API performance](https://www.openbanking.org.uk/api-performance/) | **Ingested.** August 2026 aggregate CSV: 20 metrics across 25 months (2024-08 to 2026-08). See `open_banking_profile.md`. | This downloaded CSV has no provider, brand, service or supplier dimension. Website charts may have more detail, but cannot be inferred from this file. Unweighted and weighted definitions differ; reporting coverage may change. | **Used** as separate aggregate external context; loader in `04_etl/ingest_open_banking.py`. Not redistributed (see licence note) |
| [FCA firm complaints data](https://www.fca.org.uk/data/complaints-data/firm-level), [historic releases](https://www.fca.org.uk/data/complaints-data/previous-complaints-data) | Firm/product/half-year contextual evidence of complaint volume, including context measures and reporting definitions | Complaints cover multiple causes, are lagged and cannot be mapped to synthetic incidents. Firm publication excludes reporters below 500 complaints in the period; group/joint reporting and revisions matter. | **Not used.** Considered for context; adds nothing to the selected question |

## Acquisition protocol

1. Retrieve from the publisher and preserve the raw release without editing.
2. Record URL, file name, publication/update date, retrieval timestamp, licence and SHA-256.
3. Inspect worksheet/column definitions, coverage, denominators, missingness and revision notes.
4. Decide whether each source genuinely improves the service risk decision; exclude irrelevant data.
5. Never join real bank rows to fictional supplier or incident identifiers as if entities matched.

No public source above establishes a causal link between supplier failure and customer complaints. Probability parameters for our fictional bank must be tagged as simulated assumptions or explicitly derived from its simulated records.

## Verification notes

- Open Banking reports both weighted and unweighted availability and describes a last-12-month historical download on its public page. Its notes state that since August 2026 nine providers and nineteen brands have supplied data. We must inspect the actual downloaded schema before choosing analysis units.
- FCA's 2025 H2 firm-specific release was updated 15 May 2026 following a reporting anomaly. It is available under the Open Government Licence. The source states that firms below the 500-complaint publication threshold are absent from firm-specific tables, though their figures contribute to aggregates.

## Licence note (Open Banking)

Open Banking Limited's website terms state that all rights in site material are reserved, that pages and extracts may be downloaded for personal use, and that authorship must be acknowledged. No open data licence covers the API performance statistics (the site's MIT licence covers specifications and reference applications only). This repository therefore contains the ingestion code and checksum, not the CSV or the derived monthly series. To reproduce the public panel, download the historical CSV from https://www.openbanking.org.uk/api-performance/ and run `04_etl/ingest_open_banking.py` or `08_dashboard/export_dashboard_data.py --open-banking-csv <file>`.
