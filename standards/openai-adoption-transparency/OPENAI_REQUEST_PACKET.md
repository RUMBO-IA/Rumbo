# OpenAI request packet — Adoption Transparency

## Requested capability
Add publisher-facing adoption analytics for each published app/plugin, exposed in the OpenAI developer platform and through a read-only API.

## Minimum data
- listing impressions
- current installations
- new installations by period
- uninstallations by period
- active accounts over 7 and 30 days
- total successful tool calls
- 30-day retention

## Privacy requirements
Publisher responses MUST be aggregate-only. Do not expose ChatGPT account IDs, conversations, prompts, IP addresses, emails, tool inputs, or raw credential identifiers.
Unique-user metrics SHOULD be suppressed below a configurable cohort threshold. Suppression must be explicit and must not be replaced by an estimate.

## Verification requirements
Every report SHOULD contain a canonical payload hash, key identifier, signature algorithm, signature, reporting period, generated_at timestamp, schema version, and monotonic report_revision.
The publisher MUST be able to verify the report independently without calling an undocumented internal OpenAI service.

## Correct metric semantics
An installation is a successful distribution-state event. An active user is a distinct account that invokes the app during the stated window. A tool call is an execution count. A listing impression is a discovery event. These metrics must never be presented as interchangeable.

## Why this matters
Marketplace distribution without publisher-facing adoption telemetry makes it difficult to distinguish discovery, installation, real use, retention and technical execution. A standardized aggregate report gives developers operational visibility while preserving user privacy.

## Evidence and context
OpenAI documentation states that the Plugins Directory is the primary discovery surface for workflows across ChatGPT and Codex, and that plugins may contain skills, apps and app templates.
OpenAI documentation also describes workspace-level analytics for eligible Business workspaces and compliance logging for app calls, but those are not documented as publisher-level adoption analytics for individual public apps.

## Reference implementation
RUMBO provides:
- protocol specification
- JSON Schema
- Ed25519 reference verifier
- adversarial tests
- signed test vector
- public explainer
- discovery document
- fail-closed adoption observability audit

## Open-source references
- https://github.com/RUMBO-IA/Rumbo/tree/main/standards/openai-adoption-transparency
- https://github.com/RUMBO-IA/Rumbo/pull/159
- https://rumbo.verso.fans/openai-adoption-transparency
- https://rumbo.verso.fans/schemas/openai-adoption-transparency/report-envelope-v1.json
