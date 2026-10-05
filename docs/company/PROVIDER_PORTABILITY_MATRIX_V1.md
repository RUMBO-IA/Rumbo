# RUMBO Provider Portability Matrix V1

Status: RESEARCHED DESIGN / PROVIDER APPROVALS NOT PROVEN

## Core rule

One RUMBO product, one tenant/entitlement/evidence system, multiple provider adapters.

| Provider | Distribution / partner surface | RUMBO packaging | Billing assumption | Current RUMBO status |
|---|---|---|---|---|
| OpenAI | Partner Network, Apps/Directory, Marketplace-related commercial programs, SIWC where eligible | MCP/App adapter + OpenAI annex + assessment evidence | external/direct partner billing unless explicit provider-native capability is proven | assessment resubmitted; pass/listing/SIWC commercial approval NOT_PROVEN |
| Anthropic | partner ecosystem + MCP/Claude integrations as available | MCP-compatible adapter + security/support annex | direct RUMBO commercial authority | partner/listing acceptance NOT_PROVEN |
| Google Cloud | Cloud Marketplace / partner publication paths | SaaS/API listing adapter + provisioning/entitlement integration | provider-specific marketplace procurement plus RUMBO entitlement readback | publisher/listing approval NOT_PROVEN |
| Microsoft | Commercial Marketplace + Copilot/agent ecosystem where applicable | SaaS/agent package + Microsoft annex | marketplace/transactable offer when eligible, otherwise direct | publisher/listing approval NOT_PROVEN |
| Direct customers | RUMBO web/API/MCP | canonical product | MoR/card/invoice according to region/entity | architecture exists; customer production NOT_PROVEN |

## Shared provider-independent package

Every provider receives:
- company overview;
- product description;
- architecture/data flow;
- security/privacy/responsible-AI pack;
- support and incident policy;
- pricing/commercial model;
- deployment methodology;
- evidence/claim registry;
- customer case-study evidence only when actually proven.

## Adapter-specific annex

Each annex should answer:
1. what product surface is being listed;
2. authentication method;
3. OAuth/callback URLs;
4. data accessed;
5. data retention/deletion;
6. subprocessors;
7. execution permissions;
8. billing/entitlement mapping;
9. support/escalation;
10. removal/revocation;
11. provider-specific policy compliance;
12. exact status: DRAFT / SUBMITTED / APPROVED / LISTED.

## Outreach gate

Do not send partner outreach saying “we are an OpenAI partner”, “marketplace approved”, “production proven”, “certified”, or “used by customers” unless an evidence receipt exists for the exact statement.

A safe outreach narrative before approvals is:
- vendor-neutral AI agent assurance/control-plane company;
- current public engineering evidence;
- bounded operational AI product;
- seeking technical/commercial integration or partner review;
- no implied endorsement from another provider.

## Provider-specific engineering rule

Marketplace acceptance must not create a second customer database.

All provider identities map into the same RUMBO user/tenant model and all provider commercial events map into the same canonical subscription/entitlement ledger.
