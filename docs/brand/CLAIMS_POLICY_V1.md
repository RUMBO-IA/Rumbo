# RUMBO IA Claims Policy V1

## Purpose
Prevent public copy from becoming stronger than the underlying evidence.

## Claim classes
- BUILT: implementation exists. Does not imply deployment, customer use or measured impact.
- DEMO: demonstration or simulated behavior/data. Must be visibly labeled.
- PILOT: bounded real-world evaluation. Must state scope when material.
- PRODUCTION: serving live production traffic. Requires deployment evidence.
- MEASURED: numerical result observed under a defined method, population and time window.

## Promotion rule
A claim may move to a stronger class only when its evidence receipt supports that class. Absence of evidence fails closed to the weaker class.

## Measured claims
Record metric definition, denominator, observation window, data source, exclusions, baseline where relevant and evidence pointer. Avoid percentages without denominators or dates.

## Prohibited unsupported language
Guaranteed ROI; guaranteed revenue; 100% secure; fully autonomous where supervision exists; zero risk; production-ready when only demo/pilot evidence exists; customer logos/testimonials without permission; invented user/customer counts; fabricated comparative superiority.

## Demo rule
Simulated metrics, company names, conversations and events must be identified in-context as DEMO/SIMULATED/EXAMPLE. A global footer disclaimer alone is insufficient for a misleading local presentation.

## Security language
Describe controls and scope, not absolute safety. Prefer `human-supervised`, `explicit verification boundary`, `bounded workflow`, and `security controls are documented`.

## Release gate
CLAIMS_POLICY_PASS != EVIDENCE_PASS != PUBLICATION_AUTHORITY != PRODUCTION_DEPLOYMENT.
