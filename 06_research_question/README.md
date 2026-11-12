# Research question selection after data review

The public source and the fictional internal simulation have now been profiled and examined. See `02_data/open_banking_eda_review.md` and `02_data/simulated_bank_eda_review.md`. A score of 0–2 for each criterion is an analyst judgement made after the data review, not a measured statistic.

| Candidate decision question | Data grain and quality | Decision value | Honest inference | Total / 6 |
| --- | ---: | ---: | ---: | ---: |
| Which recovery exercises should the fictional bank prioritise across services and shared suppliers under explicit disruption scenarios? | 2 | 2 | 2 | **6** |
| Can monthly supplier warnings predict a bank's next incident? | 1 | 1 | 0 | 2 |
| Did public Open Banking availability cause incidents in our bank? | 0 | 1 | 0 | 1 |
| Which real UK supplier is the highest operational risk? | 0 | 1 | 0 | 1 |

## Selected portfolio research question

**Under stated severe-but-plausible disruption and recovery assumptions, which service and shared-supplier recovery exercises should a fictional UK bank prioritise to reduce simulated impact-tolerance breaches, and how stable is that priority when the assumptions change?**

Decision owner: a fictional operational resilience committee. Unit of analysis: service-impact episode, with a distinct shared event ID for multi-service disruption. Candidate actions: specific recovery exercises or control pilots whose assumed effects, costs, responsible owners and review points will be documented before modelling. Outcome: count of simulated service episodes exceeding each illustrative impact tolerance, with scenario cost and customer reach only as separately labelled assumptions. Comparison: baseline vs interventions across parameter ranges and alternative seeds. Public Open Banking data remains an unlinked external-context panel.

Selection followed inspection of the 25-month public aggregate and the 24-month simulated internal layer, not the other way around. The question does **not** ask for real bank probabilities or evidence that a named supplier failed. Scenario effectiveness is not present in the dataset; it must be declared as a transparent assumption and stress-tested. Sminia's wayfinding paper informs how proposed exercises translate into learning and adaptation; it cannot validate their effectiveness in a bank.
