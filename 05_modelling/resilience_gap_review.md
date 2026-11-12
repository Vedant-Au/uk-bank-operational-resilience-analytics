# Recovery gap and supplier concentration: results

**Run:** `python3 05_modelling/resilience_gaps.py` on generator v1.0, default seed 280926, with seeds 280926 to 280975 for stability. Output: `02_data/processed/resilience_gaps.json` and the `recovery_*` and `supplier_*` files in `08_dashboard/data/`. All figures describe the simulated bank only.

## Why this analysis was added

The exercise comparison (`scenario_run_review.md`) could not separate card and payments rehearsals: both avoid a median of two breaches at an assumed 30% faster recovery. That result follows from the assumption. This analysis turns the question around and asks what improvement each service would *need*, which a committee can set as an exercise target and then test.

## 1. Recovery gap by service

The cut is the smallest uniform reduction in restoration time that removes the stated share of a service's breaches, rounded up.

| Service | Tolerance (min) | Breaches / episodes | Cut to halve breaches | Cut to clear all | Halve, median of 50 seeds |
|---|---:|---:|---:|---:|---:|
| Card authorisation | 90 | 8 / 13 | 30.8% | 68.1% | 31.3% |
| Everyday payments | 120 | 6 / 13 | 25.5% | 59.8% | 30.9% |
| Mobile account access | 180 | 3 / 11 | 13.1% | 28.6% | 19.9% |
| Mortgage servicing | 480 | 0 / 5 | none | none | breaches in only 4 of 50 seeds |

Reading: card authorisation carries the most breaches and needs about 31% faster restoration to halve them. That figure is stable across seeds (30.8% default, 31.3% median), so it does not depend on one lucky draw. Clearing every breach needs roughly two thirds faster recovery for card and payments, which is a capability change rather than a rehearsal outcome. Mobile access closes most of its gap with a modest improvement.

## 2. Supplier concentration

Structural stress test: a full outage of one supplier stops each dependent service for the outage length, with no failover.

| Supplier | Services | High-criticality | First breach after | All breached after | Shared events (default / seed median) |
|---|---|---:|---:|---:|---:|
| Provider Beta | Payments, Card authorisation | 2 | 90 min | 120 min | 0 / 1 |
| Provider Alpha | Payments, Mobile access | 2 | 120 min | 180 min | 1 / 1 |
| Provider Gamma | Mobile access, Mortgage | 1 | 180 min | 480 min | 1 / 1 |
| Provider Delta | Card authorisation | 1 | 90 min | 90 min | 0 / 0 |
| Provider Epsilon | Mortgage | 0 | 480 min | 480 min | 0 / 0 |

Reading: Provider Beta is the concentration point. It sits behind the two services with the tightest tolerances, it is rated low substitutability, and an outage longer than two hours breaches both. It had no shared event in the default history, which is why the replay-based exercise comparison gives shared-provider coordination almost no credit. History and structure disagree here, and structure is the better guide for a rare, high-impact event.

## What this changes in the recommendation

1. Pilot card authorisation recovery first, with an explicit target of about 30% faster restoration (the median episode would fall from 107 to roughly 74 minutes).
2. Make the shared-provider exercise specific to Provider Beta: test whether card authorisation can be restored or failed over inside 90 minutes when Beta is down.
3. Treat "clear all breaches" (60 to 70% faster) as a design question for failover and redundancy, not something a rehearsal will deliver.

## Limits

The cut is applied uniformly to every episode of a service. Real improvements are uneven: detection might speed up while supplier-side restoration does not. The stress test assumes no failover and full outage, which is the severe end of plausible. Customer bases are the generator's illustrative scale. None of these figures estimate a real bank's exposure.
