# Open Banking historical CSV: intake assessment (2026-09-28)

**Publisher:** Open Banking, https://www.openbanking.org.uk/api-performance/  
**Original file:** `Historic Data Download- csv August 2026 (CSV).csv` (downloaded from the publisher on 28 Sep 2026; kept locally and not redistributed in this repository).  
**SHA-256:** `efdaa5fd0dfcf818aadc4df5d747d90de85b965b85235f73506965248a8a476f`  
**Grain:** one published aggregate metric per month, not one provider, brand, service or supplier per row.  
**Coverage:** 2024-08 to 2026-08 inclusive, 25 consecutive months. This actual CSV is longer than the website selector's “last 12 months” label.  
**Shape:** 20 measures × 25 months = 500 numeric observations; source is wide, with measures in rows and months in columns.

## Checks performed

| Check | Observed result | Treatment |
| --- | --- | --- |
| Column count | All 21 CSV rows have 26 fields | Accept |
| Missing observations | 0 of 500 | Accept, subject to publisher definitions |
| Month headings | 25 unique consecutive YYYYMM fields | Parse as first day of observation month |
| Duplicate measure labels | 0 | Accept |
| Monthly failed calls = business + technical failures | All 25 months reconcile exactly | Preserve as intake invariant |
| Published technical-failure percentage vs technical failures / (successes + failures) | Maximum absolute difference 0.005 percentage point | Consistent with two-decimal display rounding |
| Percent ranges | Availability measures observed between 98.87% and 99.99% across series | Percentages stored on 0–100 scale |
| Units | Counts, percentages, API response time in ms | Preserve each metric's unit |

## Preliminary descriptive observations (not a research question)

- Monthly successful API calls were 1,581,848,583 in August 2024 and 2,971,328,791 in August 2026 (1.88×). The reporting population and definitions must be checked before treating that as like-for-like growth.
- August 2026 unweighted availability was 99.53%; weighted availability was 99.98%. These are differently calculated published measures and must not be averaged or substituted for one another.
- The lowest unweighted availability in the CSV is 98.87% in March 2026. Monthly aggregate availability alone does not disclose incident durations or impact-tolerance breaches.

## Analytical fit

Suitable for background trends and definitions, checking an ingestion and quality workflow, and a separate external-context dashboard panel. It cannot provide supplier concentration, operational incident root causes, a fictional bank's recovery times, or defensible probabilities of the fictional bank exceeding its impact tolerances. No linkage from this aggregate to simulated internal rows will be claimed.

The public page describes the unweighted availability as the endpoint with greatest downtime for each bank each day; its weighted measure uses each endpoint's share of daily API calls. Verify detailed methodology and any changes in reporting population before comparing distant periods.
