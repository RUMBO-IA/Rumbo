# Scope Binding Before Evidence Promotion

A small fail-closed reference implementation for preventing cross-scope evidence contamination in agentic workflows.

Related design note: [Issue #14](../../../issues/14)

## Invariant

```text
DISCOVERED
  -> QUARANTINED
  -> SCOPE_BOUND
  -> IDENTIFIED
  -> PRIMARY_EVIDENCE
  -> DIRECT_BINDING
  -> VERIFIED
```

There is no direct `DISCOVERED -> TARGET` transition.

Before `target_scope_binding=true`, target identity and downstream evidence fields are rejected rather than persisted.

## Run

```bash
python -m unittest -v test_scope_guard.py
python scope_guard.py receipt.json
```

The CLI prints one of:

- `SCOPE_UNRESOLVED`
- `NO_RESULT`
- `SCOPED_NOT_VERIFIED`
- `VERIFIED`

A control-plane "online" signal does not count as executable availability. If an advertised-online state is followed by a failed benign command handshake, the receipt fails with `TRANSPORT_RACE_ABORTED`.

## Workspace-scope adapter

`workspace_scope_guard.py` specializes the same fail-closed pattern for coding workspaces. It separates **trusted scope authority** from **observed session state** and supports environment-resolved multi-root scopes. The authority supplies an opaque `scope_id`, resolved CWD, authoritative workspace-root set, optional environment ID, auxiliary roots, and any roots that must be writable. Observed session state cannot define or expand those values. This avoids both failure directions: accepting a consistently wrong foreign workspace and rejecting a legitimate owner-provided secondary workspace.

This directly supports a regression shape for concurrent Project A / Project B sessions without claiming a Codex implementation detail or root cause.

## Adjacent OpenAI design references

These are not claims of the same bug; they are related design guidance:

- OpenAI Agents SDK notes that nested tool execution can have separate run/approval state and recommends explicit application-level isolation when nested mutation is unsafe:
  https://github.com/openai/openai-agents-python/blob/89c02c828ee8510fe9a84ee6675608193aa13b02/.agents/references/agent-definition-and-run-context.md

- The OpenAI Agents SDK maintainer evaluation framework says evidence from a linked issue should only carry over when runtime variant, provider/tool type, trigger, configuration, and user outcome actually match:
  https://github.com/openai/openai-agents-python/blob/89c02c828ee8510fe9a84ee6675608193aa13b02/.agents/skills/maintainer-review/references/evaluation-framework.md

This reference implementation generalizes that idea into an admission gate for evidence promotion.

## Relevant Codex isolation report

A materially related upstream report is [openai/codex#24224](https://github.com/openai/codex/issues/24224), which describes concurrent Codex Desktop sessions inheriting the wrong project/workspace state across projects.

This repository does **not** claim the same root cause or a Codex fix. The useful connection is an acceptance invariant: before repo-local instructions, workspace metadata, or tool execution become authoritative, the selected task/project and effective workspace scope should agree. If they do not, the session should fail closed rather than promote stale or foreign project context.

A regression matrix for that class of failure should cover concurrent Project A / Project B sessions, stale workspace metadata injection, persisted/restored state, and rejection before file or command tools receive the wrong scope.

## Codex source seam analysis

See [`CODEX_WORKSPACE_SCOPE_SEAMS.md`](./CODEX_WORKSPACE_SCOPE_SEAMS.md) for the source-level admission, runtime, and persistence seams inspected in `openai/codex`.

## Codex Thread.environments probe

`codex_thread_scope_probe.py` consumes a sanitized app-server `Thread` snapshot,
an independent scope-authority object, and `environment/status` results.

OpenAI's protocol explicitly defines `Thread.environments` as **selection** data,
independent of connection status. The probe therefore refuses to treat selection
as runtime proof. The selected environment must also report `status=ready`.

```bash
python codex_thread_scope_probe.py codex_thread_scope_snapshot.example.json
```

Expected result for the included fixture:

```json
{"decision":"RUNTIME_SCOPE_BOUND","errors":[],"ok":true}
```

Pinned protocol references:
- Thread selection field: openai/codex commit `2b554fd3f96a128be52e0d64b01f6adf16cc467a`
- Current protocol seam inspected at `8e6a44b428e31f91b21edc97904fcdf4f0931ade`

`pending`, `disconnected`, `unknown`, missing status, project mismatch, CWD mismatch,
or environment mismatch fail closed rather than being promoted as executable scope.
