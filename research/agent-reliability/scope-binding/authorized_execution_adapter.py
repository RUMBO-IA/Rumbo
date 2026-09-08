from __future__ import annotations

from typing import Any, Callable

import execution_admission_guard as admission


def execute_authorized(
    workspace_receipt: dict[str, Any],
    authority: dict[str, Any],
    request: dict[str, Any],
    effect: Callable[[], Any],
) -> dict[str, Any]:
    decision = admission.evaluate(workspace_receipt, authority, request)
    if decision.get("state") != "ALLOW":
        return {
            "state": "SAFE_STOP",
            "errors": list(decision.get("errors") or []),
        }

    try:
        result = effect()
    except Exception as exc:
        return {
            "state": "EFFECT_FAILED",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    return {"state": "EXECUTED", "result": result}
