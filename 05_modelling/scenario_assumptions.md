# Recovery exercise comparison: declared assumptions

**Decision question:** see `06_research_question/README.md`. This experiment replays incidents from the fictional generator. No observed control effects, costs or real-bank event frequencies are available. The three options below are **illustrative interventions**, not recommended controls backed by operational evidence.

| Option | Scope in simulated data | Duration multiplier: optimistic / central / cautious | What a real exercise would check |
| --- | --- | --- | --- |
| Card recovery rehearsal | S03 card authorisation episodes | 0.50 / 0.70 / 0.90 | Failover steps, handoff ownership and recovery timing. |
| Payments recovery rehearsal | S01 everyday payments episodes | 0.50 / 0.70 / 0.90 | Recovery runbook and customer communication. |
| Shared-provider coordination | Episodes with an explicit shared event ID | 0.50 / 0.70 / 0.90 | Joint escalation, supplier contact and service-level decisions. |

Each multiplier represents the *assumed* remaining duration after an effective exercise. A 0.70 multiplier means a 30% shorter impact for the eligible incident in this toy experiment. It does not prevent events or change the number of exposed customers. No supplier warning or public metric drives intervention assignment. Each option is evaluated separately, with no stacking or investment cost. The same generated incidents are used for baseline and option within every run; changes in breach counts therefore reflect only the assumed duration reduction.

**Sensitivity:** repeat the generator over 50 declared seeds (`280926` through `280975`), then compare cautious, central and optimistic effects. This is a distribution **across invented worlds**, not a confidence interval or bank outage probability. The default seed is also reported separately and never treated as representative. The ranking may reverse across runs or effect assumptions. An exercise should advance to a live pilot only after a human validates its feasibility, effort and actual recovery effects.

**Wayfinding application:** card and payments rehearsals test whether known response capability can be mobilised when coping breaks *in*; shared-provider coordination may reveal whether a new cross-service practice is needed when coping breaks *of*. See `07_strategy/scenario_wayfinding.md` for the source lens. Record a named owner, evidence from the exercise, review date and stop/change criterion before any strategic recommendation.
