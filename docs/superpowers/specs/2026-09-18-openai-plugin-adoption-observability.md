# OpenAI plugin adoption measurement

## Current boundary

RUMBO Agent Reliability v0.1.6 is skills-only. It has no MCP server, OAuth flow, remote runtime, or publisher-controlled request endpoint. Therefore the publisher cannot observe a ChatGPT account merely because the skill was installed or invoked.

OpenAI public submission documentation exposes app submission and review permissions, not a publisher-facing installation or active-user metric. Current directory search and account probes are observations, not a substitute for a platform analytics export.

## Measurement contract

1. Native OpenAI install/user metrics: use only a first-party dashboard or export directly attributable to the publisher.
2. Skills-only proxy: a disclosed landing-page event may count page visits or opt-in activations, but MUST NOT be labeled as installs, accounts, or active users.
3. Remote app/MCP telemetry: a future version may count authenticated requests and unique consented identities, with minimum collection and an updated privacy policy.
4. Every metric gets a timestamp, source, scope, freshness, and evidence reference.
5. Unknown, inaccessible, stale, or contradictory evidence remains UNKNOWN/NOT_OBSERVABLE; never infer a number.

## Required future fields

metric_name, value, unit, population, observed_at, source, evidence_ref, freshness, identity_basis, privacy_basis.

## Safety

Do not add hidden network calls to the current skills-only package. Any telemetry must be disclosed, purpose-limited, and implemented as a separately reviewed remote capability.
