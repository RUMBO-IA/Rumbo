# OpenAI Adoption Transparency Protocol v1

## Purpose
Give app/plugin publishers a trustworthy way to know how their distribution is performing without exposing user identities.

OpenAI operates the distribution layer and, for authenticated integrations, can represent a stable profile identity. OpenAI also provides workspace-level analytics for eligible Business workspaces. As of 18 September 2026, the public app/plugin submission documentation does not define a publisher-facing install/active-user analytics contract for a published app. This protocol defines that missing contract without exporting user identities.

## Design
1. OpenAI is the source of truth for platform-side distribution facts.
2. OpenAI emits an aggregate, signed adoption report for an authenticated publisher.
3. RUMBO verifies the report cryptographically and records it in an evidence ledger.
4. No raw ChatGPT user identifiers are exported to the publisher.
5. Small cohorts are suppressed; metrics carry explicit scope, period, freshness, and status.
6. A report is valid only when its signature, hash, schema, and privacy constraints pass.

## Proposed OpenAI surface
GET /v1/publishers/{publisher_id}/apps/{app_id}/adoption-report?from=...&to=...

The response is a signed envelope with: platform publisher/app identifiers, reporting period, listing impressions, installs, uninstalls, active users, tool calls, retention, data-quality metadata, and an Ed25519 attestation.

## Minimum metrics
- listing_impressions
- installations_total
- installations_new
- uninstallations
- active_users_7d
- active_users_30d
- tool_calls_total
- retention_30d

Each metric is either exact or privacy-suppressed. Suppressed metrics do not expose a hidden estimate.

## Privacy
User-level data is never exported. The platform may compute metrics from its internal account graph, but the publisher receives aggregates only. The default reference policy suppresses unique-user metrics for cohorts below 5 and permits the platform to add differential-privacy noise where needed.

## Evidence
Every report includes generated_at, reporting_period, schema version, source, key_id, algorithm, payload_sha256, and signature. RUMBO stores the report hash and verification result rather than trusting the publisher's claim.

## Governance
The protocol is intentionally vendor-neutral. OpenAI can implement the publisher API and dashboard; RUMBO provides the reference verifier, schemas, test vectors, and evidence-ledger integration. Other AI platforms can implement the same contract.

## Non-goals
This protocol does not identify individual users, expose private conversations, or guarantee business outcomes. It measures distribution and usage telemetry only.
