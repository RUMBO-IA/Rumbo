# OpenAI Partner Technical Assessment — Supporting Evidence V2

**Organization:** RUMBO IA  
**Date:** 2026-10-05  
**Status:** Evidence-bounded support for OpenAI Partner Network / technical-capability review. This document does not claim an OpenAI partner tier, specialization, certification, SIWC approval, customer production deployment, or measured customer ROI.

## Company and product boundary

RUMBO IA builds **Operational AI Systems** with human control, explicit authority boundaries and verifiable outcomes.

The strategic platform direction is an **AI Agent Assurance & Execution Control Plane**: a vendor-neutral layer for policy/preflight, state revalidation, bounded execution, effect readback, receipts, replay/idempotency controls, recovery and evidence export.

The current public product surface is intentionally narrower and organized around three lines:
1. **Revenue Recovery** — bounded commercial workflows for stalled leads, forgotten quotes, no-shows and dormant customers.
2. **Agent Reliability** — state, continuity, execution controls, readback and evidence for AI agents.
3. **Guardian** — defensive assurance, policy boundaries and auditability for higher-risk authorized workflows.

The current public commercial entry remains a bounded Revenue Recovery Sprint rather than an automatically activated recurring SaaS subscription.

## Organization identity clarification

RUMBO IA's current website and this assessment describe the **same organization and the same AI delivery practice**.

The current public company surface at `rumbo.verso.fans` identifies RUMBO IA as **Operational AI Systems** and presents three product lines: Revenue Recovery, Agent Reliability and Guardian. RUMBO IA is not presenting a separate staffing or recruiting business as its current company identity.

Any earlier public surface that could have created a staffing/recruiting impression should not be treated as the current organizational positioning or as evidence of a separate customer-AI practice. The AI systems, implementation methodology, commercial pilot intake, reliability work and assurance controls described here are all RUMBO IA work under the same company identity.

The intended-solution narrative and the current website are therefore aligned:
- one organization: RUMBO IA
- one operating thesis: human-controlled Operational AI Systems
- one strategic control layer: AI Agent Assurance & Execution Control Plane
- current public product lines: Revenue Recovery, Agent Reliability and Guardian

## Current evidence boundary

Current evidence supports:
- founder-operated engineering and product development;
- built and tested control-plane, reliability, commercial-portal and defensive-assurance components;
- controlled pilot intake and bounded commercial offer preparation;
- tenant-aware authentication/workspace architecture;
- policy, execution-receipt, MCP-call and usage-ledger surfaces;
- public evidence and claim controls.

Not claimed:
- completed customer AI/ML production deployments;
- measured customer ROI or production-impact metrics;
- production-scale OpenAI traffic;
- OpenAI Select, Advanced or Elite status;
- an OpenAI specialization in Codex, cybersecurity or agents;
- Sign in with ChatGPT commercial approval or client credentials;
- ISO 27001, SOC 2, HIPAA, PCI DSS or equivalent certification;
- recurring SaaS billing live in production.

## OpenAI platform context

The connected OpenAI Platform account currently exposes organization **Rumbo** with projects:
- **Rumbo** (initial project)
- **RUMBO-AI-DEV**

OpenAI usage is separated from RUMBO commercial billing and entitlement state.

Planned / current engineering use includes bounded prototyping and evaluation for:
- classification and summarization;
- approved business-knowledge retrieval;
- agent/tool workflows with explicit authorization;
- human approval for consequential actions;
- reliability and regression evaluation;
- recovery and final-state verification;
- Responses/agent workflows where the applicable account and product permissions are separately enabled.

No API key, secret, organization identifier or project identifier is published in this evidence document.

## Sign in with ChatGPT boundary

OpenAI documents Sign in with ChatGPT for websites as an Authorization Code + PKCE / OpenID Connect integration available to selected commercial partners through a limited trial.

RUMBO therefore treats commercial SIWC as **external-approval-gated**:
- no production SIWC button is shown without verified commercial approval and credentials;
- identity scopes are not treated as permission to access ChatGPT conversations or unrelated OpenAI resources;
- ChatGPT plan usage is a separate permission from identity;
- ChatGPT plan usage is not a payment rail for RUMBO subscription, support, storage, governance or managed-service fees.

Official reference:
- https://developers.openai.com/siwc/quickstart
- https://developers.openai.com/siwc/website

## Delivery methodology

1. Define the business outcome, accountable human owner and acceptance criteria.
2. Map systems, data, credentials, permissions, privacy constraints and sensitive actions.
3. Bind the execution to explicit authority and a fresh-state preflight.
4. Implement the smallest useful bounded workflow.
5. Evaluate deterministic and adversarial cases, including stale context, duplicate execution, partial failure, missing readback, permission errors and unknown outcomes.
6. Apply data minimization, least privilege, privacy/security checks and explicit demo/test versus production boundaries.
7. Run a controlled pilot with simulated or customer-authorized data and human supervision for consequential actions.
8. Verify intended effects through readback/evidence; API/tool success is not treated as proof of final business state.
9. Expand scope only after acceptance evidence, rollback planning and owner authorization.

## Execution-control architecture

Target execution model:

```text
request
  -> identity / tenant
  -> authority + policy preflight
  -> fresh state validation
  -> execution adapter
  -> provider/system effect
  -> destination readback
  -> receipt / evidence ledger
  -> reconciliation / recovery
```

The design separates:
- capability from authorization;
- authorization from execution;
- execution from verified effect;
- workspace identity from commercial entitlement;
- processor events from RUMBO entitlement decisions;
- public product claims from private-control authority.

Unknown or ambiguous outcome is a first-class state and is not treated as success.

## Commercial control-plane evidence

The current customer-facing candidate includes:
- account sign-in / registration backed by Supabase Auth;
- automatic profile + workspace + owner-membership provisioning on user creation;
- tenant-scoped workspace access;
- subscription-ledger-derived commercial plan display;
- MCP call history;
- billable-usage history;
- execution receipts;
- support-ticket intake;
- verified partner-record surface.

Commercial entitlement is being reconciled around the subscription/commercial ledger rather than legacy workspace metadata. A workspace placeholder such as `starter` is not treated as an active commercial plan.

The current recurring catalog is frozen as a **candidate, not live**. No recurring checkout should be inferred from catalogue files alone.

## Billing and provider boundary

RUMBO's provider-neutral billing architecture can represent:
- Stripe;
- Paddle;
- PayPal Invoice;
- Lemon Squeezy;
- Mercado Pago.

This list is architectural, not an activation claim. The existing private runtime has a Stripe adapter; non-Stripe adapters are not claimed implemented.

The target global architecture is:
- Merchant-of-Record candidate for recurring global SaaS;
- invoice/manual-payment path for bounded services and pilots;
- local payment rails only as optional regional channels;
- normalized signed provider events;
- idempotency/replay controls;
- RUMBO-owned subscription and entitlement decisions.

No live recurring products or prices are claimed approved.

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

Escalation procedure: stop the affected execution, preserve evidence/state, route to the owner, reassess scope/permissions/risk, and resume only after authority and state are reconciled.

## Security and compliance claim boundary

RUMBO IA currently claims **no external AI compliance certification**.

Engineering controls include:
- human supervision;
- explicit authorization boundaries;
- least privilege;
- data minimization;
- privacy-by-design;
- fail-closed behavior;
- RLS / tenant isolation on customer data surfaces;
- append-only evidence where appropriate;
- execution/readback receipts;
- security headers and content-security controls on public web surfaces;
- defensive security work kept separate from privileged customer-facing cyber services unless separately authorized.

RUMBO IA does **not** claim ISO 27001, SOC 2, HIPAA, PCI DSS or equivalent certification unless separately evidenced in the future.

## Partner Network alignment

OpenAI publicly describes Partner Network progression through **Select, Advanced and Elite**, with expectations around commercial performance, technical capability, co-selling participation and deployment experience, plus potential specializations in areas such as Codex, cybersecurity and agents.

RUMBO's current evidence is primarily relevant to the **technical-capability** dimension:
- agent execution boundaries;
- reliability / recovery;
- policy and evidence controls;
- defensive assurance;
- controlled commercial workflows;
- implementation methodology.

This document does **not** infer any Partner Network tier or specialization from technical work alone.

Official reference:
- https://openai.com/index/introducing-openai-partner-network/

## Current use case submitted for assessment

**RUMBO IA — Revenue Recovery with Agent Assurance controls**

Target outcome: organize fragmented customer conversations, leads, proposals and follow-ups while reducing manual operational gaps, with control-plane evidence around consequential actions.

Implementation pattern:
- AI-assisted classification/summarization;
- approved business knowledge;
- bounded workflow automation;
- explicit human approval for consequential actions;
- state revalidation;
- audit/readback controls;
- execution receipts and recovery for interrupted or ambiguous outcomes.

Current evidence class:

**BUILT / DEMO / TESTED / CONTROLLED PILOT INTAKE**

Not claimed:
- completed customer production deployment;
- measured customer ROI;
- production-scale usage;
- OpenAI certification, endorsement, tier or specialization.

## Public evidence map

- `README.md` — current company/product positioning, commercial entry and claim boundaries.
- `index.html` — Operational AI Systems surface: Revenue Recovery, Agent Reliability and Guardian.
- `docs/openai/COMMERCIAL_PLATFORM_V1.md` — strategic AI Agent Assurance & Execution Control Plane boundary and commercial architecture.
- `dashboard.html` / `portal.js` — customer control-plane candidate for workspace, subscription state, MCP calls, usage and execution receipts.
- `security.html` — defensive security / Agent Reliability scope and claim separation.
- `docs/brand/CLAIMS_POLICY_V1.md` — public claim policy.
- `docs/brand/PROFILE_COPY_V2.md` — current Operational AI Systems profile narrative.
- `docs/brand/production_lock_v1.json` — governed production-surface authority record.
- `scripts/verify_public_production_surface.py` — exact public-surface verification.
- repository CI — brand, privacy, commercial-coherence, security-header and control-authority checks.

## Open gaps before stronger partner claims

1. Complete at least one authorized customer production deployment and preserve deployment evidence.
2. Measure customer outcome/ROI with an agreed baseline before publishing impact claims.
3. Keep OpenAI Platform production usage separate from demos and evaluations.
4. Complete any OpenAI-requested commercial/technical assessment steps.
5. Obtain explicit SIWC approval/client credentials before enabling commercial SIWC.
6. Complete billing-provider onboarding and production authority before enabling recurring checkout.
7. Add compliance certifications only after separate evidence exists.

## Accuracy boundary

This document intentionally distinguishes:
- built/tested capability from customer production deployment;
- pilot intake from completed customer pilot;
- public source code from private-control authority;
- login identity from inference permission;
- payment-provider capability from provider activation;
- technical capability from OpenAI Partner Network tier or specialization;
- demos and tests from customer ROI.

Any future production, customer, certification, partner-tier, specialization, SIWC or measured-impact claim should be added only after separate evidence exists.

