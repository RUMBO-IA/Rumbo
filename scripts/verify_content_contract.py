from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = pathlib.Path("docs/brand/content_registry_v2.json")
IDENTITY_REGISTRY = pathlib.Path("docs/brand/identity_registry_v1.json")
DISTRIBUTION_LOCK = pathlib.Path("docs/brand/distribution_lock_v1.json")
CANON = pathlib.Path("docs/brand/CONTENT_CANON_V2.md")

EXPECTED_DOMAIN = "https://rumbo.verso.fans"
ALLOWED_LANES = {"RUMBO_BRAND", "PERSONAL_BRAND"}
ALLOWED_STATES = {
    "SOURCE_MATERIAL", "QUARANTINED", "CANDIDATE_SAFE",
    "READY_FOR_HUMAN_REVIEW", "PUBLISHED",
}
ALLOWED_CLAIMS = {"BUILT", "DEMO", "PILOT", "PRODUCTION", "MEASURED"}
DENIED_COPY = (
    r"\bnexo(?:\s+3\.0)?\b",
    r"\brumboia\.com\b",
    r"\b3x\b",
    r"60%",
    r"\b20\+?\s+empresas\b",
    r"\b80\s+mensajes\b",
    r"\+38%",
    r"\b100%\s+secure\b",
    r"\bguaranteed\s+roi\b",
    r"\bfully\s+autonomous\b",
    r"\bdiagn[oó]stico\s+grat(?:is|uito)\b",
)

def _load_json(root: pathlib.Path, rel: pathlib.Path) -> dict:
    path = root / rel
    if not path.is_file():
        raise ValueError(f"missing required file: {rel.as_posix()}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _identity_allowed(root: pathlib.Path, name: str, role: str) -> bool:
    data = _load_json(root, IDENTITY_REGISTRY)
    identities = data.get("identities", {})
    for canonical, roles in identities.items():
        if canonical.casefold() == name.casefold():
            return role in roles
    return False

def verify(root: pathlib.Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        data = _load_json(root, REGISTRY)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"content registry invalid: {exc}"]

    if data.get("schema_version") != 2:
        errors.append("content registry schema_version must be 2")
    if data.get("canonical_public_domain") != EXPECTED_DOMAIN:
        errors.append("canonical public domain drift")
    if data.get("auto_publish") != "NO_GO":
        errors.append("AUTO_PUBLISH must remain NO_GO")
    if data.get("distribution_authority_ref") != DISTRIBUTION_LOCK.as_posix():
        errors.append("distribution authority ref must bind distribution_lock_v1.json")

    try:
        distribution = _load_json(root, DISTRIBUTION_LOCK)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return errors + [f"distribution authority invalid: {exc}"]
    distribution_status = distribution.get("overall_status")
    if distribution_status not in {"PARTIAL_PASS", "PASS"}:
        errors.append("distribution authority status invalid")

    items = data.get("items")
    if not isinstance(items, list) or not items:
        return errors + ["content registry items must be a non-empty list"]

    ids = [item.get("id") for item in items if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("content item ids must be unique")

    for item in items:
        if not isinstance(item, dict):
            errors.append("content item must be an object")
            continue
        item_id = item.get("id", "<missing>")
        lane = item.get("lane")
        state = item.get("publication_state")
        claim = item.get("claim_class")

        if lane not in ALLOWED_LANES:
            errors.append(f"{item_id}: invalid lane")
        if state not in ALLOWED_STATES:
            errors.append(f"{item_id}: invalid publication_state")
        if claim not in ALLOWED_CLAIMS:
            errors.append(f"{item_id}: invalid claim_class")

        identity = item.get("identity")
        if lane == "RUMBO_BRAND":
            if identity != "RUMBO IA":
                errors.append(f"{item_id}: RUMBO_BRAND identity must be RUMBO IA")
            elif not _identity_allowed(root, identity, "PUBLIC_EXPRESSION"):
                errors.append(f"{item_id}: identity is not admitted as PUBLIC_EXPRESSION")
        if lane == "PERSONAL_BRAND" and identity == "RUMBO IA":
            errors.append(f"{item_id}: personal lane cannot inherit RUMBO IA identity")

        copy = item.get("copy", "")
        if state == "CANDIDATE_SAFE" and not isinstance(copy, str):
            errors.append(f"{item_id}: CANDIDATE_SAFE copy must be text")
        if isinstance(copy, str):
            for pattern in DENIED_COPY:
                if re.search(pattern, copy, re.I):
                    errors.append(f"{item_id}: denied legacy/unsupported copy pattern: {pattern}")

        evidence = item.get("evidence_refs")
        if not isinstance(evidence, list):
            errors.append(f"{item_id}: evidence_refs must be a list")
            evidence = []

        if state == "READY_FOR_HUMAN_REVIEW" and not evidence:
            errors.append(f"{item_id}: review-ready item requires evidence")
        if state in {"READY_FOR_HUMAN_REVIEW", "PUBLISHED"} and distribution_status != "PASS":
            errors.append(f"{item_id}: release state requires DISTRIBUTION=PASS")
        if claim == "MEASURED" and state not in {"QUARANTINED", "SOURCE_MATERIAL"}:
            if not item.get("metric_receipt"):
                errors.append(f"{item_id}: MEASURED claim requires metric_receipt")
        if state == "PUBLISHED":
            receipt = item.get("publication_receipt")
            if not isinstance(receipt, str) or not receipt.strip():
                errors.append(f"{item_id}: PUBLISHED requires publication_receipt")

    canon_path = root / CANON
    if not canon_path.is_file():
        errors.append("CONTENT_CANON_V2.md missing")
    else:
        canon = canon_path.read_text(encoding="utf-8-sig")
        for required in (EXPECTED_DOMAIN, "AUTO_PUBLISH = NO_GO", "PERSONAL_BRAND != RUMBO_BRAND"):
            if required not in canon:
                errors.append(f"content canon missing invariant: {required}")

    return errors


if __name__ == "__main__":
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        sys.exit(1)
    print("PASS: RUMBO content contract")
