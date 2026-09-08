from __future__ import annotations

from typing import Any

import autonomy_surface_guard
import workspace_scope_guard


def evaluate(workspace_receipt: dict[str, Any], action_authority: dict[str, Any], action_request: dict[str, Any]) -> dict[str, Any]:
    scope = workspace_scope_guard.evaluate_workspace_scope(workspace_receipt)
    action = autonomy_surface_guard.evaluate(action_authority, action_request)

    errors = sorted(set(scope.get("errors", [])) | set(action.get("errors", [])))
    allowed = scope.get("ok") is True and action.get("state") == "ALLOW" and not errors
    return {
        "state": "ALLOW" if allowed else "SAFE_STOP",
        "errors": errors,
        "scope_decision": scope.get("decision"),
        "action_decision": action.get("state"),
    }
