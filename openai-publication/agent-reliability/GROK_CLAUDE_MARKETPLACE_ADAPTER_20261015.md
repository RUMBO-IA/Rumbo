# RUMBO Agent Reliability — Grok Build / Claude interoperability candidate

This **review-only candidate** reuses the already published RUMBO five-skill package under `openai-publication/agent-reliability/plugin/`, with a new `.grok-plugin/plugin.json` discovery manifest. No new MCP endpoints, credentials, hooks, scripts, model runtime or external writes are introduced.

## Source identity
- Package version: **0.1.6** (historical public source only).
- Source base: RUMBO-IA/Rumbo commit `a16c59802d696bf5d155e07c11d22347f3f88149`.
- Current separately held private Plugin Creator version **0.3.12** is **not** included, not represented as identical, and not declassified.
- The five existing skills are canonical-state-recovery, deep-research-reconcile, goal-loop-controller, execute-verify-close, audit-final-state.
- Read the existing source receipt and `FINAL_READINESS.json`. Their historical checks do not prove the present candidate was installed in Grok Build.

## Not for marketplace submission until gates close
1. Organization owner authorizes the exact public distribution license. Public repository governance explicitly says the public Open Lab license is not yet in effect. **NO claimed license.**
2. Confirm platform manifest discovery and installation from **the exact branch commit**, and run clean local tests and in-client acceptance. No real Grok Build / Claude test was performed by this documentation change.
3. Reviewer confirms product-specific security scope, no prompt injection in skill files, and that source is appropriate for third-party distribution.
4. If accepted, use xAI `xai-org/plugin-marketplace`: fork, append one `source: url` entry pinned to the **full verified SHA** and the source `path: openai-publication/agent-reliability/plugin`, generate `.grok-plugin/plugin-index.json` with official script, validate and open PR. **No external PR is submitted by this RUMBO branch.**
5. For Anthropic, follow its authenticated plugin developer submission flow separately; Grok adaptation is not Claude marketplace approval.
6. No claim that OpenAI private registration or an AppDeploy READY diagnostic is marketplace publication.

## Boundaries
- Skills only; **no MCP tools**, `postinstall`, arbitrary shell hook or cloud secrets.
- Not a runtime release, not production, no partner endorsement, no customer reference.
- This path is supplementary to, and cannot promote, canonical RUMBO control.
- Exact submission must reference an owner-authorized license and evidence of tests before clicking any truth attestations.
