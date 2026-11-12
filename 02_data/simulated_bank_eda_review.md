# Fictional bank simulation: warehouse QA and EDA

**Reviewed:** 2026-09-28. Default generator v1.0, seed `280926`, 24 months (September 2024 to August 2026). This is an invented exercise dataset, not evidence of a real institution's incidents, exposures, probabilities or losses. The generator uses no public Open Banking values.

The generator, validator, loader and `03_sql/006_simulated_quality.sql` were run on local PostgreSQL 18. The load recorded batch 2, `simulated_internal`, 179 raw source rows, 4 services, 5 suppliers, 8 dependencies, 120 monthly supplier observations and 42 incident-impact rows in both staging and core. The dependency, shared-event grouping and monthly-calendar exception queries each returned zero rows. Regenerating the default seed reproduces the same manifest checksums.

## What the 42 rows show under the chosen assumptions

| Fictional service | Illustrative tolerance, minutes | Incident-impact rows | Rows beyond tolerance | Median duration, minutes |
| --- | ---: | ---: | ---: | ---: |
| Everyday payments | 120 | 13 | 6 | 92 |
| Mobile account access | 180 | 11 | 3 | 104 |
| Card authorisation | 90 | 13 | 8 | 107 |
| Mortgage servicing | 480 | 5 | 0 | 62 |

The total is 17 simulated tolerance breaches across 42 service-impact rows. The four shared-impact rows belong to **two** shared event IDs; consequently 42 rows represent 40 unique simulated events, assuming all other rows are distinct local events. Do not sum impacts as independent supplier failures. Card authorisation has the highest count above its shorter illustrative tolerance, which is a feature of the chosen threshold and random draw, not evidence that a real card service is most vulnerable.

Three fictional providers each support two services; two support one each. This is a mapping exercise, not observed concentration in a real bank. Supplier monthly warnings were drawn independently of incident events and must not be promoted as a predictive risk signal. The generated customer and loss fields use arbitrary service scale and duration factors; present these only as scenario inputs with sensitivity ranges.

## Quality gate and modelling limits

The seed and complete input manifest are stored with generated local files; their CSV hashes are checked again before loading. Loader reuse of the same manifest is a no-op, while a different seed is refused in the current database. A second independent run with a different seed belongs in a fresh database. The generator has no transaction denominator, uptime exposure adjustment, control test history, actual recovery capability or observed customer impact. Do not estimate real bank breach likelihood from 17/42, claim a causal supplier effect, fit an incident-warning predictor, or infer external aggregate month-to-bank relationships.

For the next decision product, define alternative recovery exercises and their assumed efficacy **before** comparing results. Report plausible ranges and demonstrate how rankings change under stress and alternative assumptions. A new question can be selected now that the internal grain and observed synthetic distributions are known; keep all recommendations explicitly conditional on simulation assumptions and operational validation.
