# Internal data design: specification, not observations

All records in the internal-bank layer will be simulated. The generator needs a versioned random seed, named distributions, relationships, justified bounds, sensitivity ranges, and a record of every deliberate anomaly introduced for quality checks.

## Entities and grain

| Entity | Grain | Important rules |
| --- | --- | --- |
| Service | One fictional business service | Impact tolerance is an illustrative policy assumption in minutes. |
| Supplier | One fictional provider | Do not use real firms' names in ways that imply incidents or responsibility. |
| Service–supplier dependency | One relationship per service and supplier | Shared provider can support multiple services; prevents a comma-separated supplier list. |
| Incident | One service-impact episode | `supplier_id` is optional: absence does not prove internal cause. An incident affecting two services requires an explicit shared event ID. |
| Supplier observation | One supplier per observation date | Availability percentage and warning indicator have documented definitions. |
| Control test | One control/service at a testing date | Test failure is distinguished from whether the control caused an actual incident. |

## Design risks to resolve before generating rows

- Choose a monthly versus daily observation calendar, period and incident sample size; do not tune them to manufacture a desired answer.
- Define exposure denominators (service operating minutes, transactions), incident severity, overlapping outages and censoring.
- Specify detection and restoration timestamps so negative intervals cannot be silently accepted.
- Introduce shared events explicitly; avoid counting the same multi-service disruption as independent root events.
- Define dependencies and recovery controls before drawing outcomes; document which assumptions create any apparent pattern.
- Keep a provenance column or manifest identifying every simulated input; keep public datasets in a distinct schema.

## Version 1 assumptions (before looking at synthetic outcomes)

- Calendar: 24 complete UTC months, September 2024 through August 2026. A service is assumed continuously exposed; there are no transaction volumes or customer-level records, so incident counts and durations are descriptive only. Events starting in a month are assigned to that month; none are censored at the window boundary.
- Four fictional services and five anonymous suppliers. Service dependencies and illustrative impact tolerances are declared in the generator, not inferred from public data. A shared event has one event ID and one row per affected service. Supplier IDs on incidents indicate **assigned scenario origin**, not proof of causality.
- Every month, the generator draws 0–3 service-local events and separately attempts one shared supplier event with probability 0.16. Draws use Python's seeded pseudorandom generator. Incident duration is a bounded log-normal draw (10–900 minutes), detection happens between start and restoration, and affected customers and losses are illustrative functions of duration and service scale, not empirical estimates.
- Each supplier has one simulated monthly observation with availability 98.0–100.0% and a warning indicator drawn independently at probability 0.12. These observations are deliberately **not** predictive of simulated incidents; no association from this version may be advertised as a validated early-warning model.
- No deliberate corrupted rows are put in the production example. Error screening tests alter a temporary copy and ensure rejection. Reproduce by preserving generator version, seed, source assumptions and file checksums. Later sensitivity work varies event rates, duration distribution and dependencies explicitly, with no estimated real-bank probability.

The public series is never used to generate bank incidents. Exploratory patterns in synthetic data show how the method works; they are not real-world discoveries.
