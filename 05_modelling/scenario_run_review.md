# First scenario comparison: interpret with restraint

**Run:** local source manifest for generator v1.0, seed `280926`; `compare_exercises.py` with 50 synthetic seeds from `280926` to `280975`. Reproduced with `python3 05_modelling/compare_exercises.py`; the figures match `08_dashboard/data/scenarios.csv`. All duration effects are **assumed**, not observed. See `scenario_assumptions.md` and the machine-readable output generated in `02_data/processed/scenario_comparison.json`.

| Exercise | Default seed: avoided breaches (cautious / central / optimistic) | Across 50 invented seeds: central median [min, max] | Central runs with zero avoided |
| --- | --- | --- | ---: |
| Card recovery rehearsal | 1 / 3 / 6 | 2 [0, 5] | 6 of 50 |
| Payments recovery rehearsal | 2 / 3 / 3 | 2 [0, 6] | 9 of 50 |
| Shared-provider coordination | 0 / 0 / 0 | 0.5 [0, 4] | 25 of 50 |

The default baseline has 17 tolerance exceedances among 42 service impacts. Across the 50 alternative generated worlds, baseline breaches range from 5 to 19, with median 12. This spread comes from different invented event draws. It is **not** uncertainty estimated from a bank's historical data. A zero benefit for shared-provider coordination in the default replay reflects the two generated shared events and their durations; it cannot establish that coordinating with providers is unimportant.

## Provisional strategy implication

If an exercise programme could pilot one service-level runbook first, card and payments recovery are both reasonable **test candidates** under these assumptions. The numerical comparison does not distinguish them at the central median, and no implementation effort, feasibility, genuine event frequency or measured control effect is available. Choose a pilot only after an operator confirms operational relevance and records an owner, effort, exercise criteria and observed recovery timing. Shared-provider coordination remains a separate cross-service resilience exercise, especially because rare shared incidents can affect more than one service.

This follows Sminia's wayfinding lens as a project application: rehearse existing practical coping, identify capabilities missing during a breakdown *in* coping, and, where existing arrangements fail *of* coping, test a small new cross-service coordination practice. Revisit the priority after the exercises produce actual evidence. Never label these scenario counts as real risk reductions or a compliant bank's measured tolerance outcomes.
