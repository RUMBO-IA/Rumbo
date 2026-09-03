# Codex workspace-scope seams

This is design/test analysis, not an upstream patch or root-cause claim.

## 1. Session admission / UI synchronization

At source snapshot `b27a6321fa1a1dbb48e019d1d1296d2a13dc4261`,
`codex-rs/tui/src/chatwidget/session_flow.rs` applies a `ThreadSessionState` by
copying session CWD and runtime workspace roots into configuration/permissions,
then refreshing repo-local context and submitting pending initial input.

Permalink:
https://github.com/openai/codex/blob/b27a6321fa1a1dbb48e019d1d1296d2a13dc4261/codex-rs/tui/src/chatwidget/session_flow.rs

A workspace-binding admission check is therefore most valuable before those
observed session values acquire downstream authority.

## 2. Runtime versus owner-resolved workspace roots

Recent upstream commit `7625bd56657da7ce6d96b6d27e983e568757cdbc`
("Honor environment-resolved workspace roots") moves effective workspace roots
into `EnvironmentConfig`, while preserving selection roots for thread-owned
configuration and allowing a ready environment owner to supply resolved roots.
Commit:
https://github.com/openai/codex/commit/7625bd56657da7ce6d96b6d27e983e568757cdbc

This invalidates an overly simple invariant such as
`workspace_roots == [project_root]`. A safer reference model separates:

- trusted task/project scope identity;
- trusted environment-owner resolution;
- observed session/runtime state.

The reference guard therefore accepts an authoritative multi-root set and
rejects observed roots outside that set.

## 3. Thread settings versus environment configuration

Commit `d75c85f65139aa9245a96d05642a0a5d2bae436a`
("Separate thread settings from environment configuration") keeps environment-
owned permissions/workspace roots effective without persisting them as
thread-owned settings.

Commit:
https://github.com/openai/codex/commit/d75c85f65139aa9245a96d05642a0a5d2bae436a

That separation matters for repair semantics: a contamination detector should
not blindly overwrite environment-owned scope while trying to repair stale
thread-owned state.
## 4. App-server observability

Commit `2b554fd3f96a128be52e0d64b01f6adf16cc467a` exposes loaded thread
environment selections in app-server responses, including working directory and
runtime workspace roots.

Commit:
https://github.com/openai/codex/commit/2b554fd3f96a128be52e0d64b01f6adf16cc467a

This creates a useful read-only observation surface, but observed environment
state still should not define its own trust authority.

## 5. Tool authorization boundary

Commit `fe140d4c8e7d47950d4d2e35ff7c58e55b744f65` evaluates `apply_patch`
targets using the active filesystem-policy context and workspace roots.

Commit:
https://github.com/openai/codex/commit/fe140d4c8e7d47950d4d2e35ff7c58e55b744f65

This reinforces the fail-closed placement: scope mismatch should be detected
before repo-local tool authorization consumes a foreign or stale root set.

## Reference acceptance invariant

```text
trusted scope identity
+ trusted environment resolution
        ↓
observed session / turn / permission state
        ↓
exact authorized root-set comparison
        ↓
SCOPE_BOUND or SCOPE_UNRESOLVED
```
