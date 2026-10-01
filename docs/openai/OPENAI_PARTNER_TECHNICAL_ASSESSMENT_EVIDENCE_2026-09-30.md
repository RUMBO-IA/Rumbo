# OpenAI Partner Technical Assessment — Supporting Evidence

**Organization:** RUMBO IA  
**Date:** 2026-09-30  
**Status:** Evidence-bounded support for the reopened OpenAI Partner Network Technical Capability Assessment.

## Organization and current commercial state

RUMBO IA is a founder-operated AI systems company in Argentina. The current commercial product direction is **human-controlled AI CRM and workflow automation for small businesses in Argentina and Latin America**.

Current state:
- one founder / technical practitioner;
- product and engineering prototypes are built and tested in controlled environments;
- controlled pilot intake is active / being prepared;
- **0 completed customer AI/ML production deployments are claimed**;
- **0 customer ROI or production-impact metrics are claimed**;
- no OpenAI endorsement, certification, or partner-tier status is claimed beyond what OpenAI explicitly confirms;
- no external AI or hyperscaler certification is currently claimed.

## Intended solution

RUMBO IA is building a bounded operating layer for customer-facing commercial workflows, including lead and conversation organization, proposal/follow-up workflows, approved business knowledge, revenue-recovery workflows, supervised AI assistance, tool use behind explicit authorization boundaries, human approval for consequential actions, and evidence/readback/recovery controls.

The goal is not fully autonomous business execution. The product is designed around explicit supervision and bounded automation.

## OpenAI platform usage and intended use

The connected OpenAI Platform account currently exposes organization **Rumbo** and project **RUMBO-AI-DEV**.

Planned / current engineering usage includes bounded prototyping and evaluation of OpenAI-powered assistants or agents for classification and summarization, business-knowledge retrieval, workflow assistance, tool-mediated actions with explicit permission checks, human-approval gates, reliability/regression evaluation, recovery, and final-state verification.

No production-traffic volume, customer count, or production-scale OpenAI workload is asserted here.

## Delivery methodology

1. Define the business outcome, accountable human owner, and acceptance criteria.
2. Map systems, data, credentials, permissions, privacy constraints, and sensitive actions.
3. Implement the smallest useful bounded prototype.
4. Evaluate deterministic and adversarial cases, including stale context, duplicate execution, partial failure, missing readback, permission errors, and unknown outcomes.
5. Apply data minimization, least privilege, privacy/security checks, and explicit demo/test versus production boundaries.
6. Run a controlled pilot with simulated or customer-authorized data and human supervision for consequential actions.
7. Verify the intended effect through readback/evidence; API/tool success is not treated as proof of final business state.
8. Expand scope only after acceptance evidence, rollback planning, and owner authorization.

## Governance and Responsible AI

**Designated owner:** Founder / Partner Admin.

Operational governance is fail-closed:
- capability does not equal authorization;
- authorization does not equal execution;
- execution does not equal verified outcome;
- sensitive actions require explicit scope and human approval;
- unknown or ambiguous outcome is not treated as success;
- least privilege is preferred;
- retries account for idempotency / duplicate-effect risk;
- recovery preserves evidence and re-establishes authority before continuing;
- final state is verified through readback where applicable.

Escalation procedure: stop the affected execution, preserve evidence/state, route to the owner, reassess scope/permissions/risk, and resume only after authorization and state are reconciled.

## Security and compliance claim boundary

RUMBO IA currently claims **no external AI compliance certification**.

Current engineering controls include human supervision, explicit authorization boundaries, least privilege, data minimization, privacy-by-design, fail-closed behavior, audit/evidence records, security headers/content-security controls on public web surfaces, and separate defensive security work that is not exposed as a privileged customer-facing cyber service.

RUMBO IA does **not** claim ISO 27001, SOC 2, HIPAA, PCI DSS, or equivalent certification unless separately evidenced in the future.

## Current use case submitted for assessment

**RUMBO IA human-controlled CRM / Revenue Recovery**

Target outcome: organize fragmented customer conversations, leads, proposals, and follow-ups while reducing manual operational gaps.

Implementation pattern: AI-assisted classification/summarization, approved business knowledge, bounded workflow automation, explicit human approval for consequential actions, and audit/readback controls.

Current evidence class: **BUILT / DEMO / TESTED / CONTROLLED PILOT INTAKE**.

Not claimed:
- completed customer production deployment;
- measured customer ROI;
- production-scale usage;
- OpenAI certification or endorsement.

## Public evidence map

- `README.md` — current company/product positioning and claim boundaries.
- `apps/landing-publica/index.html` — current public commercial product surface.
- `security.html` — defensive security scope and explicit separation from the commercial product.
- `docs/brand/CLAIMS_POLICY_V1.md` — public claim policy and prohibited unsupported claims.
- `docs/brand/MESSAGING_V1.md` — canonical product/capability descriptions.
- `docs/brand/production_lock_v1.json` — governed production-surface authority record.
- `scripts/verify_public_production_surface.py` — exact public-surface verification.
- repository tests and CI — deterministic regression and governance checks.

## Accuracy boundary

This document intentionally distinguishes built/tested capability from production deployment, pilot preparation from customer production, internal/defensive engineering from commercial customer services, public source code or submitted upstream work from accepted third-party contributions, and technical capability from external certification.

Any future production, customer, certification, partner-tier, or measured-impact claim should be added only after separate evidence exists.
