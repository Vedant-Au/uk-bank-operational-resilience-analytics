# Project scope

- **Organisation:** explicitly fictional UK retail bank.
- **Audience:** Head of Operational Risk, COO and Risk Committee.
- **Problem:** critical customer services rely on applications, people and third parties; disruptions may exceed management-defined impact tolerances.
- **Units of analysis:** service, supplier dependency, incident and observation period; maintain different grains and avoid double counting shared incidents.
- **Candidate services:** payments, account transfers, digital access and customer authentication. Inclusion is provisional until simulation design.
- **Decisions:** identify material service and supplier concentrations; compare feasible monitoring, failover and recovery investments under uncertainty.
- **Time horizon:** illustrative historical simulation plus forward-looking scenarios. Set exact dates and parameter ranges before generating data.
- **Boundaries:** no customer-level personal data, no confidential bank material, no attribution of public complaints to synthetic incidents.

## Research-question gate

The management problem above is deliberately broad. The specific research question was written only after acquiring the data, checking its quality, building the warehouse and reviewing exploratory results (see `06_research_question/README.md`). Model complexity followed the selected decision.

## Regulatory context

The FCA's operational resilience guidance and SYSC 15A inform the vocabulary of important business services, impact tolerances, mapping and scenario testing. Our example tolerance values will be illustrative bank policy assumptions, not regulatory thresholds.

- https://www.fca.org.uk/firms/operational-resilience
- https://handbook.fca.org.uk/handbook/SYSC/15A/
