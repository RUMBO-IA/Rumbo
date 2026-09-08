from __future__ import annotations

from typing import Any


def _clean_set(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {str(value).strip() for value in values if isinstance(value, str) and value.strip() and value != "*"}


def evaluate(authority: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    surfaces = authority.get("surfaces") if isinstance(authority, dict) else None
    surface = str(request.get("surface") or "").strip()
    capability = str(request.get("capability") or "").strip()
    effect = str(request.get("effect") or "").strip()

    if not isinstance(surfaces, dict) or not surface or surface not in surfaces or surface == "*":
        errors.append("SURFACE_AUTHORITY_REQUIRED")
        return {"state": "SAFE_STOP", "errors": errors}

    grant = surfaces.get(surface)
    if not isinstance(grant, dict):
        errors.append("SURFACE_AUTHORITY_REQUIRED")
        return {"state": "SAFE_STOP", "errors": errors}

    capabilities = _clean_set(grant.get("capabilities"))
    effects = _clean_set(grant.get("effects"))
    if not capability or capability not in capabilities:
        errors.append("CAPABILITY_AUTHORITY_MISMATCH")
    if not effect or effect not in effects:
        errors.append("EFFECT_AUTHORITY_MISMATCH")

    return {"state": "ALLOW" if not errors else "SAFE_STOP", "errors": errors}
