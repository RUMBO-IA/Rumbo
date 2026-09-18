# OpenAI implementation proposal

## Product change
Add a Publisher Adoption panel to the OpenAI developer platform and expose the same data through a read-only API.

## Publisher-visible metrics
| Metric | Meaning | Privacy rule |
| --- | --- | --- |
| listing_impressions | Listing detail views | Aggregate |
| installations_total | Current successful installs | Aggregate |
| installations_new | Successful installs in period | Suppress small cohorts |
| uninstallations | Successful removals in period | Suppress small cohorts |
| active_users_7d | Unique accounts that invoked the app in 7 days | Suppress small cohorts |
| active_users_30d | Unique accounts that invoked the app in 30 days | Suppress small cohorts |
| tool_calls_total | Total successful tool calls | Aggregate |
| retention_30d | Share of new users active again in 30 days | Suppress small cohorts |

## API contract
`GET /v1/publishers/{publisher_id}/apps/{app_id}/adoption-report?from=...&to=...`

Return the protocol envelope defined in `schemas/report-envelope-v1.json`. Authentication proves publisher ownership; response data contains no ChatGPT user identifiers.

## Trust model
1. OpenAI computes counts from its authoritative distribution and usage systems.
2. OpenAI signs the canonical payload with an Ed25519 key.
3. The publisher downloads the report and verifies the signature and payload hash.
4. RUMBO or another verifier records the hash, source, period, and verification outcome in an evidence ledger.
5. Report revisions are append-only and identified by a monotonic revision number so stale dashboards cannot silently overwrite history.

## Privacy model
User-level conversations, prompts, emails, IP addresses, account IDs, and tool inputs are never exported.
Unique-user metrics are suppressed below a minimum cohort, with the platform free to add differential-privacy noise for higher-risk populations.
Suppression is explicit; the API never substitutes a guessed number.

## Correct semantics
An installation is a successful distribution-state event. An active user is an account that invoked the app during the stated window. A tool call is an execution count. Listing impressions are discovery signals. None of these metrics is interchangeable with another.

## Governance
OpenAI owns the first-party measurement; RUMBO provides an independently auditable verification layer. The protocol is open so other AI platforms can publish equivalent reports without requiring access to another platform's user identities.

## Acceptance tests
- Same signed payload verifies deterministically.
- Any changed payload fails hash or signature verification.
- A protected unique-user metric below the configured threshold fails closed unless suppressed.
- A report with an end date after generated_at fails.
- A report exporting user-level data fails.
- An issuer other than OpenAI fails.
- A publisher can compare two reporting periods without losing the earlier evidence.
