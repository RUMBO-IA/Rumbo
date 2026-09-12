#!/usr/bin/env python3
"""Fail-closed workspace-scope admission guard for agent sessions.

Trusted scope authority is external to observed session state. The authority may
resolve to multiple workspace roots (for example, an environment owner).
"""

from __future__ import annotations

import json
import posixpath
import re
import sys
from pathlib import Path
from typing import Any


_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:/")
_WINDOWS_UNC = re.compile(r"^//[^/]+/[^/]+(?:/|$)")
_WINDOWS_EXTENDED = re.compile(r"^//\?/(?:[A-Za-z]:/|UNC/)", re.I)


def normalize_path(value: str) -> str:
    raw = value.strip().replace("\\", "/")
    if not raw:
        return ""
    normalized = posixpath.normpath(raw)
    if len(normalized) > 1:
        normalized = normalized.rstrip("/")
    if (
        _WINDOWS_DRIVE.match(normalized)
        or _WINDOWS_UNC.match(normalized)
        or _WINDOWS_EXTENDED.match(normalized)
    ):
        normalized = normalized.casefold()
    return normalized

def _normalized_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [normalize_path(str(v)) for v in values if str(v).strip()]


def _normalized_set(values: Any) -> set[str]:
    return set(_normalized_list(values))


def _authority_values(authority: dict[str, Any]) -> dict[str, Any]:
    legacy_root = normalize_path(str(authority.get("project_root") or ""))
    scope_id = str(authority.get("scope_id") or legacy_root).strip()
    resolved_cwd = normalize_path(
        str(authority.get("resolved_cwd") or legacy_root)
    )
    resolved_roots = _normalized_list(authority.get("resolved_workspace_roots"))
    if not resolved_roots and legacy_root:
        resolved_roots = [legacy_root]

    return {
        "scope_id": scope_id,
        "cwd": resolved_cwd,
        "workspace_roots": resolved_roots,
        "auxiliary_roots": _normalized_set(
            authority.get("allowed_auxiliary_roots")
        ),
        "required_writable_roots": _normalized_set(
            authority.get("required_writable_roots")
        ),
        "environment_id": str(authority.get("environment_id") or "").strip(),
        "source": str(authority.get("source") or "").strip(),
    }

def validate_workspace_scope(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    authority = receipt.get("scope_authority")
    if not isinstance(authority, dict):
        return ["SCOPE_AUTHORITY_REQUIRED"]

    expected = _authority_values(authority)
    expected_roots = set(expected["workspace_roots"])

    if not expected["scope_id"]:
        errors.append("SCOPE_AUTHORITY_ID_REQUIRED")
    if not expected["source"]:
        errors.append("SCOPE_AUTHORITY_SOURCE_REQUIRED")
    if not expected["cwd"]:
        errors.append("SCOPE_AUTHORITY_CWD_REQUIRED")
    if not expected_roots:
        errors.append("SCOPE_AUTHORITY_WORKSPACE_ROOTS_REQUIRED")
    if not expected["required_writable_roots"].issubset(
        expected_roots | expected["auxiliary_roots"]
    ):
        errors.append("AUTHORITY_REQUIRED_WRITABLE_OUTSIDE_SCOPE")

    forbidden_observed = (
        "allowed_auxiliary_roots",
        "resolved_workspace_roots",
        "required_writable_roots",
    )
    for field in forbidden_observed:
        if field in receipt:
            errors.append(f"OBSERVED_AUTHORITY_FIELD_FORBIDDEN:{field}")

    observed_scope_id = str(
        receipt.get("selected_scope_id")
        or receipt.get("selected_project_root")
        or ""
    ).strip()
    session_cwd = normalize_path(str(receipt.get("session_meta_cwd") or ""))
    turn_cwd = normalize_path(str(receipt.get("first_turn_cwd") or ""))
    workspace_roots = _normalized_set(receipt.get("workspace_roots"))
    writable_roots = _normalized_set(receipt.get("writable_roots"))
    observed_environment_id = str(receipt.get("environment_id") or "").strip()

    advertised = receipt.get("transport_advertised_online") is True
    handshake = receipt.get("transport_handshake") is True
    if advertised and not handshake:
        errors.append("TRANSPORT_RACE_ABORTED")

    if not observed_scope_id:
        errors.append("SELECTED_SCOPE_REQUIRED")
    elif expected["scope_id"] and observed_scope_id != expected["scope_id"]:
        errors.append("SELECTED_SCOPE_AUTHORITY_MISMATCH")

    if expected["environment_id"]:
        if observed_environment_id != expected["environment_id"]:
            errors.append("ENVIRONMENT_AUTHORITY_MISMATCH")

    if expected["cwd"] and session_cwd != expected["cwd"]:
        errors.append("SESSION_CWD_SCOPE_MISMATCH")
    if expected["cwd"] and turn_cwd != expected["cwd"]:
        errors.append("FIRST_TURN_CWD_SCOPE_MISMATCH")

    if not workspace_roots:
        errors.append("WORKSPACE_ROOTS_REQUIRED")
    elif expected_roots and workspace_roots != expected_roots:
        errors.append("WORKSPACE_ROOTS_SCOPE_MISMATCH")

    allowed_writable = expected_roots | expected["auxiliary_roots"]
    foreign_writable = writable_roots - allowed_writable
    if foreign_writable:
        errors.append("FOREIGN_WRITABLE_ROOT_PRESENT")

    missing_required = expected["required_writable_roots"] - writable_roots
    if missing_required:
        errors.append("REQUIRED_WRITABLE_ROOT_MISSING")

    if receipt.get("contaminated") is True:
        errors.append("CONTAMINATED_SCOPE_REQUIRES_REBIND")

    return sorted(set(errors))


def evaluate_workspace_scope(receipt: dict[str, Any]) -> dict[str, Any]:
    errors = validate_workspace_scope(receipt)
    if errors:
        return {
            "ok": False,
            "decision": "SCOPE_UNRESOLVED",
            "errors": errors,
        }
    return {"ok": True, "decision": "WORKSPACE_SCOPE_BOUND", "errors": []}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: workspace_scope_guard.py RECEIPT.json", file=sys.stderr)
        return 64
    receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = evaluate_workspace_scope(receipt)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
