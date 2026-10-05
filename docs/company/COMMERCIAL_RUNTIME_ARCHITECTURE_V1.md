# RUMBO Commercial Runtime Architecture V1

Status: CANDIDATE / NON-PRODUCTION

## Existing stack

### Public/application layer
- Vercel project: `rumbo-ia-publica`
- Git repository: `RUMBO-IA/Rumbo`
- current verified custom domain: `rumbo.verso.fans`
- current Vercel team plan observed: Hobby

### System-of-record layer
Existing Supabase project currently includes RLS-enabled tables for:
- `rumbo_tenants`
- `subscriptions`
- `rumbo_pricing_versions`
- `rumbo_policy_decisions`
- `rumbo_execution_receipts`
- `rumbo_usage_events`
- `rumbo_mcp_calls`
- `rumbo_billing_accounts`
- `rumbo_support_tickets`
- `rumbo_partner_records`
- `rumbo_invoices`
- `rumbo_invoice_items`
- `rumbo_payment_events`

The latest security-advisor read returned no security lints. This proves current schema/security posture only; it does not prove production readiness or customer traffic.

## Target runtime

```text
Client / ChatGPT / Claude / Copilot / Gemini / API
                |
          Identity/OAuth
                |
          RUMBO API Gateway
                |
           MCP Gateway
                |
      Authority + Policy Engine
                |
          Execution Adapter
                |
        Effect Readback
                |
       Execution Receipt
                |
     Usage / Billing Ledger
                |
     Subscription / Entitlement
                |
       Customer Dashboard
```

## Tenant authority

Every customer-scoped record must bind to a tenant/workspace through an explicit key or provable parent path.

Authorization data must not rely on user-editable metadata.

For browser/data-API access:
- RLS remains mandatory on exposed tables;
- ownership/tenant predicates are required, not only `TO authenticated`;
- update policies require both visibility and resulting-row checks;
- privileged server keys must never be exposed to clients.

## Execution authority

A provider tool call is not authority.

Required chain:
1. actor identity;
2. tenant;
3. entitlement;
4. requested intent;
5. policy/preflight decision;
6. execution identity/idempotency key;
7. provider operation ID;
8. post-effect readback;
9. execution receipt;
10. billable event only after the configured billing rule is satisfied.

## Billing authority

Separate:
- RUMBO subscription/service fees;
- OpenAI/other model usage paid by RUMBO;
- provider-sponsored or plan-backed usage when explicitly supported;
- marketplace procurement attribution;
- taxes/refunds handled by merchant/payment provider.

The canonical entitlement must live in RUMBO, not in a marketplace UI.

## Support authority

Email is transport; `rumbo_support_tickets` is the support system of record.

A support ticket should minimally bind:
- ticket_id;
- tenant/workspace;
- requester identity;
- category;
- severity;
- subject;
- description;
- created/updated timestamps;
- owner;
- state;
- reproduction/evidence references;
- linked incident or execution receipt;
- resolution and closure evidence.

## Provider adapter contract

Each provider adapter must implement:
- identity mapping;
- OAuth/callback configuration;
- product/listing metadata;
- entitlement lookup;
- invocation identity;
- usage/metering mapping;
- webhook/readback verification;
- disconnect/revocation;
- support/provider escalation references.

Provider-specific state must never silently elevate RUMBO authority.
