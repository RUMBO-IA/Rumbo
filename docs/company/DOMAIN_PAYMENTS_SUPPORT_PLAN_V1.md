# RUMBO Domain, Payments and Support Plan V1

Status: DECISION CANDIDATE / NO PURCHASE / NO BILLING ACTIVATION

## Domain decision

Do not hard-cut `rumbo.verso.fans`.

Use an alias-first migration:
1. register/select new canonical domain only after approval;
2. attach to Vercel and verify TLS;
3. keep `rumbo.verso.fans` active;
4. publish canonical URLs and redirects;
5. configure SPF/DKIM/DMARC;
6. create corporate support/security/privacy/billing/sales addresses;
7. migrate OAuth redirect URIs and marketplace callbacks;
8. verify every provider readback;
9. deprecate the legacy domain only after a defined coexistence period.

## Current candidate domains

Availability/pricing readbacks on 2026-10-05 showed:
- `rumbosystems.com` available, approximately USD 11.25 first year and renewal via one provider readback;
- `rumboops.com` available, approximately USD 11.25 first year and renewal via one provider readback;
- `rumbo.systems` available; semantically strong but higher renewal;
- `rumbo.run` available; low first-year price but materially higher renewal;
- `rumboia.co` available.

Availability and pricing change. Recheck before purchase.

## Naming risk

A separate active LATAM/Argentina AI business was found using the name “Rumbo IA” and domain `rumbo.chat`.

This is not a legal/trademark conclusion. It is enough to require:
- Argentina INPI search;
- domain/social confusion review;
- company-name differentiation decision;
- no domain purchase until the identity risk is consciously accepted.

Current preferred naming candidates for clarity:
1. RUMBO Systems / `rumbosystems.com`
2. RUMBO Ops / `rumboops.com`
3. RUMBO / `rumbo.systems`

## Payments

### Baseline
Do not depend on marketplace-native billing.

### Preferred international strategy
Merchant of Record first:
- Lemon Squeezy: candidate for international digital/SaaS sales and tax handling; eligibility/KYB must be confirmed for the actual RUMBO entity.
- Paddle: candidate MoR; seller eligibility/KYB and product approval must be confirmed.

### Not a current primary assumption
Direct Stripe account for an Argentina-based entity should not be treated as available until the exact legal entity and country eligibility are provider-confirmed.

### Regional option
Mercado Pago may be useful for local/regional collection, but should not become the only global B2B billing rail.

## Payment integration contract

`checkout -> provider event -> signature verification -> idempotent payment-event record -> invoice/subscription update -> entitlement recompute -> readback -> customer-visible state`

Never grant durable entitlement from an unverified browser redirect alone.

## Support v1

### Customer-facing addresses
Target aliases:
- support@
- billing@
- security@
- privacy@
- sales@

### Operator workflow
Gmail may remain the human operator inbox during the early stage.

Gmail labels are not ticket authority. Every customer case must become or link to a canonical support ticket.

### Email transport
Current Resend readback on 2026-10-05:
- `rumbo.verso.fans`: status FAILED; sending enabled; receiving disabled.
- `mail.rumbo.verso.fans`: status PENDING; sending enabled; receiving disabled.

Therefore transactional/corporate mail must not be described as production-ready until DNS verification succeeds.

### Low-cost receiving option
A custom-domain forwarding layer may route aliases to the existing Gmail inbox, while outbound transactional mail can use a verified sending provider. Keep reception and sending independently verifiable.

## Support policy v1

Until staffing exists, do not promise 24/7 human support.

Publish:
- normal business support window;
- security-report path;
- severity definitions;
- acknowledgement targets as objectives, not contractual SLAs unless actually operational;
- incident-update cadence;
- billing/refund escalation.

## Incident states

`REPORTED -> TRIAGED -> CONTAINED -> INVESTIGATING -> MITIGATED -> RESOLVED -> CLOSED`

Every incident should bind evidence, affected tenants, timeline, owner, remediation and final-state verification.
