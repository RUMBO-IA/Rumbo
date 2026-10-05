# RUMBO Partner & Enterprise Readiness Master V1

Status: CANDIDATE / NON-PRODUCTION
Date: 2026-10-05
Canonical tracker: GitHub issue #278

## Purpose

Package RUMBO as one evidence-first enterprise company surface that can be reviewed by OpenAI and adapted to Anthropic, Google Cloud, Microsoft and other distribution ecosystems without forking the core product.

## Company thesis

RUMBO builds a vendor-neutral AI Agent Assurance & Execution Control Plane.

Control sequence:

`Intent -> Authority -> Preflight -> Execution -> Readback -> Falsification -> Closure`

Commercial wedge:

Human-controlled operational AI workflows, initially CRM / Revenue Recovery, using the same control, entitlement, audit and evidence primitives.

## Current evidence boundary

PROVEN:
- public company/product surface exists;
- OpenAI Technical Capability Assessment was resubmitted on 2026-10-01 after OpenAI reopened it;
- current assessment state is RESUBMITTED_AWAITING_OPENAI_READBACK;
- OpenAI Platform organization `Rumbo` and projects `Rumbo` + `RUMBO-AI-DEV` are visible to the connected account;
- OpenAI plugin `rumbo-coding-agent-reliability` exists privately;
- Vercel project `rumbo-ia-publica` exists and is linked to this repository;
- `rumbo.verso.fans` is a verified project domain;
- Supabase already contains tenant, subscription, policy, execution-receipt, usage, MCP, billing, support, partner, invoice and payment-event tables with RLS enabled;
- current Supabase security advisor returned no security lints.

NOT PROVEN:
- Technical Capability Assessment pass;
- Select tier;
- Partner Locator listing;
- OpenAI Marketplace acceptance;
- Sign in with ChatGPT commercial approval;
- public OpenAI plugin/app listing;
- customer production deployment;
- paid customer;
- customer ROI;
- production-scale OpenAI traffic;
- external compliance certification.

## OpenAI acceptance package

The OpenAI package must contain one consistent story across website, assessment, email and repository:

1. Company identity and legal/contact surface.
2. Capability matrix using BUILT / TESTED / PILOT / PRODUCTION / MEASURED.
3. Customer-work matrix with only evidenced work.
4. Intended solution architecture.
5. OpenAI product usage map.
6. Implementation methodology.
7. Security/privacy/data-handling package.
8. Support and escalation model.
9. Deployment/readback evidence.
10. Claim registry showing each public assertion and its receipt.
11. Exact distinction between Partner Admin access, assessment pass, tier, listing, co-sell and customer status.

## Enterprise company package

Required canonical artifacts:

- Company overview / one-pager.
- Product architecture and data flow.
- Security overview and responsible AI policy.
- Privacy, Terms, DPA-ready data processing terms, retention/deletion and subprocessors.
- Incident response and business continuity.
- Support/SLA/escalation policy.
- Pricing/commercial model.
- Customer onboarding/offboarding.
- Payment/refund/cancellation policy.
- Provider annexes for OpenAI, Anthropic, Google and Microsoft.
- Evidence register.

## Commercial authority model

Provider marketplace or payment status is not RUMBO's canonical commercial authority.

Canonical sequence:

`Provider/payment event -> verified webhook/readback -> RUMBO billing ledger -> subscription -> entitlement -> service authorization`

Invariants:

- PAYMENT_SUCCESS != ENTITLEMENT_UNTIL_READBACK.
- APP_AVAILABLE != MARKETPLACE_ACCEPTED.
- MARKETPLACE_ACCEPTED != CUSTOMER.
- CUSTOMER != PAID.
- BUILD_PASS != PRODUCTION.
- SUBMITTED != PASSED != SELECT != LISTED != COSELL.

## Distribution strategy

Build one core runtime and multiple adapters:

- OpenAI Apps/MCP/SIWC adapter.
- Anthropic/Claude MCP-compatible adapter.
- Google Cloud Marketplace / Gemini ecosystem adapter.
- Microsoft Commercial Marketplace / Copilot agent adapter.
- Generic OAuth/MCP/API adapter for direct customers.

The adapters may differ in authentication, packaging, metering or listing metadata. They must not fork tenant, support, entitlement, evidence or execution authority.

## Immediate P0 closure gates

1. Preserve one public positioning: Operational AI Systems + Agent Assurance.
2. Close OpenAI evidence gaps without inventing customer claims.
3. Finish trust-center/legal/support pages.
4. Validate payment-provider KYB eligibility without activation/spend.
5. Wire payment events to canonical entitlement in a non-production lane.
6. Wire support intake to canonical support-ticket state.
7. Decide company/domain identity after conflict check.
8. Keep legacy domain alive during migration.
9. Produce provider-specific annexes.
10. Obtain provider-authored assessment/listing decisions before changing public claims.

## Spend and production law

`NEW_EXTERNAL_SPEND_USD=0` unless explicitly approved.
No domain purchase, paid hosting upgrade, billing activation, marketplace submission or production promotion is authorized by this document.
