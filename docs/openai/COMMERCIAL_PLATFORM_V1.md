# RUMBO OpenAI Commercial Platform V1

Status: implementation candidate on non-production branch. Production promotion is explicitly out of scope.

## Evidence states

- PROVEN: supported by current official OpenAI documentation or current repository evidence.
- PARTIAL: supported with material limitations.
- REQUIRES_OPENAI_APPROVAL: available only to selected/approved commercial partners.
- NOT_PROVEN: no current authoritative evidence for the claimed capability.
- FUTURE_OPTION: architecture seam only; not a public capability.

## Reconciled OpenAI facts

1. OpenAI Partner Network is a distinct program for building, co-selling and delivering AI solutions.
2. OpenAI Marketplace is distinct from Partner Network. Eligible enterprise customers may apply part of an existing OpenAI commitment toward eligible partner products; customers contract and pay the partner directly and OpenAI reconciles the commitment.
3. Sign in with ChatGPT (SIWC) supports identity and optional ChatGPT plan usage as separate permissions.
4. Commercial SIWC is limited to selected commercial partners. RUMBO must not advertise availability until approved and configured.
5. Plus/Pro users in participating apps may authorize eligible AI requests against included ChatGPT plan usage and, when available and explicitly enabled, ChatGPT credits.
6. RUMBO subscription, infrastructure, MCP, governance, storage and premium-service charges remain separate from ChatGPT plan usage/credits.
7. DIRECT_RUMBO_WALLET_CHARGE = NOT_PROVEN. Do not expose a checkout claiming direct debit of a ChatGPT wallet.

Official references:
- https://openai.com/business/partners/
- https://openai.com/business/marketplace/
- https://developers.openai.com/siwc
- https://developers.openai.com/siwc/quickstart
- https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites

## Product boundary

RUMBO's strategic product is an AI Agent Assurance & Execution Control Plane. Commodity capabilities such as login, database, billing transport and basic MCP hosting are supporting infrastructure, not the moat.

Target flow:

Client / ChatGPT / Agent / API
-> Identity Gateway
-> RUMBO API Gateway
-> MCP Gateway
-> Authority + Policy Engine
-> Execution Adapter
-> Effect Readback
-> Execution Receipt
-> Usage Ledger
-> Billing
-> Customer Dashboard

Control-plane and data-plane concerns must remain separable.

## Identity

Canonical RUMBO identity record is internal and provider-neutral.

Supported design:
- email identity
- Google identity
- ChatGPT/OpenAI identity (REQUIRES_OPENAI_APPROVAL for commercial SIWC)
- future SSO/SAML/OIDC providers

Account linking must be explicit. Provider identity does not replace RUMBO user/org records.

Required protections:
- authorization code + PKCE where supported
- state and nonce validation
- issuer/audience validation
- JWKS validation
- secure server-side session
- CSRF protection
- account-link confirmation
- revocation/disconnect handling
- tenant-aware authorization after authentication

## Multi-tenant model

Core entities:
users, identities, organizations, organization_members, projects, environments,
api_keys, mcp_clients, mcp_servers, mcp_tools, plans, subscriptions, entitlements,
usage_events, mcp_calls, ai_usage_events, billing_accounts, invoices, invoice_items,
payments, pricing_versions, support_tickets, audit_events, execution_receipts,
policy_decisions, effect_readbacks, consents, partner_records.

All tenant-owned rows require organization_id or a provable parent path to one. Production database must enforce RLS or equivalent isolation.

## MCP commercial gateway

Every billable call must produce an immutable metering event with:
request_id, trace_id, organization_id, project_id, actor/client, api_key_id,
server/tool, arguments_hash, started_at, completed_at, outcome, latency_ms,
billable_units, price_version, unit_price, amount, currency, policy_decision_id,
execution_receipt_id and effect_readback status.

Billing invariant:
one idempotency key -> at most one billable usage event.

Do not bill protocol success as successful execution if the effect readback fails.

## Billing separation

Maintain separate ledgers for:
1. RUMBO fees.
2. OpenAI API usage paid by RUMBO, when applicable.
3. SIWC ChatGPT plan-backed eligible AI usage, when approved.
4. SIWC credits-backed eligible AI usage, when approved.
5. Enterprise Marketplace commitment attribution, when applicable.

Never merge these into a single “OpenAI balance”.

BillingProvider abstraction should support direct card/invoice providers without coupling metering to one processor.

## Support

Required support surfaces:
- help center/docs
- support tickets
- billing disputes
- security contact
- incident/status page
- enterprise escalation

Support AI may read only tenant-authorized account, usage, receipt and incident data. No cross-tenant free-form access.

## Partner directory

Internal partner states:
APPLIED -> UNDER_REVIEW -> APPROVED -> ACTIVE -> SUSPENDED/REMOVED.

Public labels must remain separate:
- RUMBO Partner
- OpenAI Partner Network Member
- OpenAI Marketplace Product

The latter two require explicit verified evidence.

## Trust Center

Required before enterprise claims:
Security, Privacy, Terms, DPA, subprocessors, retention/deletion,
responsible disclosure, incident response, continuity/DR, status/history,
security contact and AI governance description.

Never claim SOC 2 / ISO 27001 / other certification without the actual report/certificate.

## P0 implementation order

1. Provider-neutral identity + organizations/RBAC.
2. Tenant-safe PostgreSQL schema and RLS.
3. MCP gateway authentication/authorization.
4. Append-only usage ledger + idempotency.
5. Execution receipt/effect-readback linkage.
6. Billing provider abstraction.
7. Usage/Billing/Receipts dashboard.
8. Support + status/security contacts.
9. Partner directory with evidence-gated labels.
10. SIWC adapter behind feature flag; disabled until approved credentials exist.

## OpenAI readiness gates

Partner Network:
- legal entity and website readiness
- customer delivery capability
- security/support evidence
- measurable customer outcomes
- application submitted != approved

Marketplace:
- partner waitlist/application
- eligible product acceptance
- enterprise procurement readiness
- direct partner contracting/billing
- Marketplace listing != all products eligible

SIWC:
- client ID granted
- callback URLs registered
- security review complete
- identity flow verified
- optional plan usage permission separately verified
- commercial availability remains gated

## NEXT_SAFE_ACTION

Implement database/metering primitives and evidence registry on a non-production branch. Do not change the production deployment binding or advertise OpenAI partner/Marketplace/SIWC status until verified approval evidence exists.
