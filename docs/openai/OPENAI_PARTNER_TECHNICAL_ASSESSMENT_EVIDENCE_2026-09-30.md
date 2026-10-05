# OpenAI Partner Technical Capability Assessment — Supporting Evidence

**Organization:** RUMBO IA  
**Evidence date:** 2026-10-05  
**Assessment state:** `RESUBMITTED_AWAITING_OPENAI_READBACK`  
**Partner tier claim:** `NOT_PROVEN`

## Assessment status and claim boundary

OpenAI Partner Support informed RUMBO IA on September 30, 2026 that the Technical Capability Assessment had not passed and reopened it for resubmission. The feedback identified a mismatch between the website presentation reviewed at that time and the customer AI delivery practice described in the assessment. Partner Support stated that, if the assessment passes, RUMBO IA will be placed into the Select tier.

RUMBO IA resubmitted the assessment on October 1, 2026 after reconciling the public positioning and supporting evidence. As of this evidence date, RUMBO IA has not received a confirmed pass/readback for that resubmission.

Therefore:
- authenticated Partner Portal / Partner Admin access is not represented as a Partner tier;
- Technical Assessment pass is not claimed;
- Select tier is not claimed;
- OpenAI endorsement, certification, co-sell approval, Marketplace approval, or Sign in with ChatGPT commercial approval is not claimed.

The official RUMBO IA identity for this evidence is the company surface at `rumbo.verso.fans` and the approved business contact `sebastian@rumbo.verso.fans`. RUMBO IA is not a staffing or recruiting company.

## Organization and current commercial state

RUMBO IA is an early-stage, founder-operated AI systems company in Argentina.

The company thesis is a vendor-neutral **AI Agent Assurance & Execution Control Plane**: an operational layer for systems that act through tools, credentials, state, infrastructure, and business processes while preserving explicit authority, fail-closed execution, evidence, recovery, and final-state verification.

A bounded commercial use case is the human-controlled CRM / Revenue Recovery workflow for small and medium businesses. That use case provides a concrete operating surface for the same control-plane principles.

Current evidence boundary:
- controlled software, tests, public product surfaces, and pilot-intake infrastructure exist;
- no completed customer AI/ML production deployment is claimed;
- no paid-customer count is claimed here;
- no customer ROI or production-impact metric is claimed;
- no production-scale OpenAI traffic is claimed;
- no external AI/security compliance certification is claimed.

## Current system architecture

The control model separates:

`Intent → Authority → Preflight → Execution → Readback → Falsification → Closure`

The implementation is designed so that tool availability, a provider API response, or requested intent is not treated as proof of a completed real-world result.

Current engineering surfaces include:
- explicit policy/authority boundaries;
- human approval for consequential actions;
- tenant-scoped customer workspaces;
- durable execution and recovery state;
- idempotency / replay controls;
- execution receipts and effect readback;
- MCP/tool-call records;
- usage and commercial ledgers;
- support/audit surfaces;
- fail-closed production and provider gates;
- exact-SHA verification for governed public changes.

## Customer account and tenant controls

The current customer account surface uses Supabase authentication and tenant-scoped database controls.

For a newly created authenticated user, the current onboarding function creates:
1. a profile;
2. a workspace;
3. an owner workspace membership.

Commercial plan authority is deliberately separate from workspace identity. The customer dashboard derives a visible commercial plan from the RLS-protected subscription ledger rather than from legacy workspace metadata.

The customer surface can display tenant-scoped usage, MCP calls, and execution receipts. These controls are engineering evidence; they are not evidence of customer production deployment or revenue.

## Commercial and billing controls

RUMBO distinguishes:
- product identity / workspace tenancy;
- commercial subscription state;
- entitlement decisions;
- provider payment events;
- RUMBO usage/accounting records.

The current billing architecture can represent multiple provider roles while keeping actually implemented adapters explicit. No provider is considered active merely because the domain can represent it.

The recurring product catalog is frozen only as a **non-live candidate**. Creating live products/prices, activating a Merchant of Record, or enforcing customer billing requires separate provider verification and production authority.

RUMBO fees remain separate from OpenAI API charges, ChatGPT plan usage, ChatGPT credits, or any Marketplace/partner attribution.

## OpenAI platform context and intended use

The connected OpenAI Platform context currently exposes:
- organization: **Rumbo**;
- project: **Rumbo**;
- project: **RUMBO-AI-DEV**.

Current/planned OpenAI usage is bounded to implementation and evaluation patterns such as:
- classification and summarization;
- approved business-knowledge retrieval;
- agent/workflow assistance;
- tool-mediated actions behind explicit permissions;
- human-approval gates;
- reliability and regression evaluation;
- recovery and final-state verification.

No production volume or customer-scale OpenAI workload is asserted.

## Sign in with ChatGPT boundary

RUMBO may evaluate Sign in with ChatGPT as an identity option, but the public product remains fail-closed until the required commercial eligibility and credentials are actually granted.

Identity sign-in, ChatGPT plan usage, API billing, and RUMBO commercial fees are separate permissions/accounting domains. None is treated as an implicit substitute for another.

## Delivery methodology

1. Define the business outcome, accountable human owner, scope, and acceptance criteria.
2. Map systems, data, credentials, permissions, privacy constraints, and consequential actions.
3. Implement the smallest bounded prototype.
4. Test deterministic and adversarial cases, including stale state, duplicates, partial failure, missing readback, permission errors, and unknown outcomes.
5. Apply least privilege, data minimization, security/privacy checks, and explicit demo/test/production boundaries.
6. Run controlled work only with simulated data or customer-authorized data and appropriate human supervision.
7. Verify intended effects through readback/evidence; execution success is not treated as final-state proof.
8. Expand authority only after evidence, rollback/recovery planning, and owner authorization.

## Governance and Responsible AI

Operational rules include:
- capability does not equal authorization;
- authorization does not equal execution;
- execution does not equal verified outcome;
- sensitive actions require explicit authority and scope;
- unknown or ambiguous outcomes are not treated as success;
- retries account for idempotency and duplicate-effect risk;
- recovery preserves evidence before continuing;
- final state is verified through readback where applicable.

Escalation is fail-closed: stop the affected execution, preserve evidence/state, reconcile scope and permissions, and resume only after authority and state are re-established.

## Security and compliance claim boundary

RUMBO IA currently claims no external AI compliance certification.

Engineering controls include:
- tenant boundaries / RLS where applicable;
- least privilege;
- human supervision;
- data minimization;
- CSP and security headers on public surfaces;
- append-only/evidence-oriented records where applicable;
- explicit provider and production gates;
- defensive security evaluation that does not target unauthorized external systems.

RUMBO IA does **not** claim ISO 27001, SOC 2, HIPAA, PCI DSS, or equivalent certification unless separately evidenced later.

## Current assessment use case

**RUMBO IA — Human-controlled Revenue Recovery on the Agent Assurance control plane**

Target outcome: help a business organize customer conversations, leads, proposals, follow-up and recovery workflows while keeping consequential actions supervised and auditable.

Implementation pattern:
- AI-assisted classification/summarization;
- approved knowledge;
- bounded workflow automation;
- explicit authorization and human approval;
- subscription/entitlement separation;
- execution receipts and readback;
- recovery for partial/unknown outcomes.

Evidence class:

`BUILT / TESTED / CONTROLLED-CANDIDATE / NO CUSTOMER PRODUCTION CLAIM`

## Public evidence map

- `README.md` — current company/product positioning and claim boundaries.
- `index.html` — public commercial product surface.
- `login.html`, `dashboard.html`, `portal.js` — customer account/control-plane surface.
- `refund.html`, `terms.html`, `privacy.html` — commercial/legal surfaces.
- `security.html` — defensive security scope.
- `docs/brand/CLAIMS_POLICY_V1.md` — evidence/claim policy.
- `docs/brand/production_lock_v1.json` — governed production binding.
- `docs/control-authority-anchor-v1.json` — public authority anchor.
- repository tests and CI — deterministic regression, privacy, security-header, commercial-coherence and authority checks.

## Accuracy boundary

This document intentionally distinguishes:
- built/tested capability from customer production deployment;
- pilot/candidate readiness from a paid production customer;
- authenticated Partner Portal access from a Partner tier;
- Technical Assessment resubmission from Technical Assessment pass;
- product identity from payment/entitlement authority;
- public source code or upstream submissions from accepted third-party contributions.

Any future customer-production, revenue, ROI, Partner tier, OpenAI approval, certification, or measured-impact claim must be added only after separate evidence exists.
