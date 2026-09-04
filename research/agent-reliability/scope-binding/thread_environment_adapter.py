#!/usr/bin/env python3
"""Adapt Codex Thread.environments selection snapshots to scope evidence."""

from __future__ import annotations

from typing import Any

from workspace_scope_guard import evaluate_workspace_scope


def evaluate_thread_environments(
    authority: dict[str, Any],
    environments: list[dict[str, Any]] | None,
    *,
    runtime_connected: bool,
    effective_writable_roots: list[str] | None = None,
) -> dict[str, Any]:
    if environments is None:
        return {
            "ok": False,
            "decision": "THREAD_UNLOADED",
            "errors": ["THREAD_ENVIRONMENTS_UNAVAILABLE"],
        }

    expected_id = str(authority.get("environment_id") or "").strip()
    selected = next(
        (
            env
            for env in environments
            if str(env.get("environmentId") or "").strip() == expected_id
        ),
        None,
    )
    if selected is None:
        return {
            "ok": False,
            "decision": "SCOPE_UNRESOLVED",
            "errors": ["ENVIRONMENT_AUTHORITY_MISMATCH"],
        }

    if not runtime_connected:
        return {
            "ok": False,
            "decision": "SELECTION_ONLY",
            "errors": ["RUNTIME_CONNECTION_NOT_PROVEN"],
        }

    receipt = {
        "scope_authority": authority,
        "selected_scope_id": authority.get("scope_id"),
        "environment_id": selected.get("environmentId"),
        "session_meta_cwd": selected.get("cwd"),
        "first_turn_cwd": selected.get("cwd"),
        "workspace_roots": selected.get("runtimeWorkspaceRoots"),
        "writable_roots": effective_writable_roots or [],
        "transport_advertised_online": True,
        "transport_handshake": True,
        "contaminated": False,
    }
    result = evaluate_workspace_scope(receipt)
    if not result["ok"]:
        return result
    return {"ok": True, "decision": "RUNTIME_SCOPE_BOUND", "errors": []}
