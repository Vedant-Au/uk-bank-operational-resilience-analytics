# Public Open Banking intake and EDA review

**Reviewed:** 2026-09-28. **Input:** the downloaded historical CSV (SHA-256 `efdaa5fd0dfcf818aadc4df5d747d90de85b965b85235f73506965248a8a476f`). **Execution:** `03_sql/004_open_banking_quality.sql` and `005_open_banking_eda.sql` run on local PostgreSQL 18. The mart returned 25 monthly rows, no month with a metric count other than 20, and the five lowest-availability months below. An independent CSV rescreen found 500 numeric observations and no blocking issues.

## Descriptive findings

| Measure | Observation | Interpretation limit |
| --- | --- | --- |
| Unweighted availability | Minimum 98.87% in March 2026; mean of 25 published monthly percentages 99.5684% | Arithmetic mean of published monthly aggregates, not an estimate of continuous uptime or a bank's impact-tolerance compliance. |
| Weighted availability | 99.83% in March 2026; the difference from unweighted availability that month is 0.96 percentage point | Different publisher calculation; do not substitute one for the other or interpret the gap as a supplier incident. |
| Successful API calls | 1,581,848,583 in August 2024; 2,971,328,791 in August 2026 (1.878 times the first count) | Descriptive endpoints, not like-for-like demand growth without reporting-population and definition checks. |
| Total failed calls | Highest count 15,308,660 in March 2026 | A large aggregate count does not identify the failure source or affected customers. |
| Response time | Published monthly series ranges from 324 ms (December 2025) to 381 ms (May 2026) | This source does not show tail latency, provider differences, or transaction impact. |

The five lowest **unweighted** availability months, as returned by the PostgreSQL mart:

| Month | Unweighted % | Weighted % |
| --- | ---: | ---: |
| March 2026 | 98.87 | 99.83 |
| October 2025 | 99.25 | 99.80 |
| November 2025 | 99.32 | 99.87 |
| September 2024 | 99.34 | 99.55 |
| June 2026 | 99.35 | 99.80 |

## Quality decision and next dependency

**Public source intake:** suitable for a clearly separate external-context panel and a reproducible warehouse demonstration. The raw CSV has 25 consecutive months, 20 expected measures, no missing numeric cells, and all 25 months satisfy the failed-call split reconciliation. The mart contains 25 monthly rows. Reuse review (Nov 2026): the publisher's website terms reserve all rights and allow downloads for personal use, with no open data licence, so the monthly series is used locally and not redistributed here.

**At this public-source review, the question gate was still open.** No supplier identifier, fictional bank service, incident duration, recovery time, or dependency edge exists in the public CSV. The later internal simulation review and question selection are recorded in `02_data/simulated_bank_eda_review.md` and `06_research_question/README.md`. Do not turn this public EDA into a claim about real bank vulnerabilities or a bank-specific strategic recommendation.
