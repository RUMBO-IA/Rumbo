#!/usr/bin/env python3
"""Generic fail-closed scope-provenance gate for agent evidence receipts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PRE_SCOPE_FORBIDDEN = (
    "target_identity",
    "primary_evidence",
    "direct_binding",
)

VERIFIED_REQUIRED = (
    "transport_handshake",
    "target_scope_binding",
    "target_scope_evidence",
    "target_identity",
    "primary_evidence",
    "direct_binding",
)

def _present(value: Any) -> bool:
    return value not in (None, "", False, [], {})


def validate(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    advertised = receipt.get("transport_advertised_online") is True
    handshake = receipt.get("transport_handshake") is True
    scope_bound = receipt.get("target_scope_binding") is True
    contaminated = receipt.get("contaminated") is True
    decision = receipt.get("promotion_decision")

    if advertised and not handshake:
        errors.append("TRANSPORT_RACE_ABORTED")

    if contaminated:
        if _present(receipt.get("target_identity")):
            errors.append("CONTAMINATED_TARGET_MUST_RESET")
        if decision == "VERIFIED":
            errors.append("CONTAMINATED_PROMOTION_FORBIDDEN")

    if not scope_bound:
        for field in PRE_SCOPE_FORBIDDEN:
            if _present(receipt.get(field)):
                errors.append(f"UNSCOPED_FIELD_FORBIDDEN:{field}")

        if decision == "VERIFIED":
            errors.append("UNSCOPED_PROMOTION_FORBIDDEN")
    elif not _present(receipt.get("target_scope_evidence")):
        errors.append("SCOPE_EVIDENCE_REQUIRED")

    if decision == "VERIFIED":
        for field in VERIFIED_REQUIRED:
            if not _present(receipt.get(field)):
                errors.append(f"VERIFIED_MISSING:{field}")

    return sorted(set(errors))


def evaluate(receipt: dict[str, Any]) -> dict[str, Any]:
    errors = validate(receipt)
    if errors:
        return {"ok": False, "decision": "NO_RESULT", "errors": errors}

    if receipt.get("promotion_decision") == "VERIFIED":
        return {"ok": True, "decision": "VERIFIED", "errors": []}

    if receipt.get("target_scope_binding") is True:
        return {"ok": True, "decision": "SCOPED_NOT_VERIFIED", "errors": []}

    return {"ok": True, "decision": "SCOPE_UNRESOLVED", "errors": []}


def _load(path: str | None) -> dict[str, Any]:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return json.load(sys.stdin)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", nargs="?")
    args = parser.parse_args()

    result = evaluate(_load(args.receipt))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
