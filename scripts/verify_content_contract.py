from __future__ import annotations

import json
import pathlib
import re
import sys

try:
    from scripts import verify_brand_contract as brand
except ImportError:  # direct execution: python scripts/verify_content_contract.py
    import verify_brand_contract as brand

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = pathlib.Path("docs/brand/content_registry_v2.json")
DISTRIBUTION_LOCK = pathlib.Path("docs/brand/distribution_lock_v1.json")
CANON = pathlib.Path("docs/brand/CONTENT_CANON_V2.md")

EXPECTED_DOMAIN = "https://rumbo.verso.fans"
ALLOWED_LANES = {"RUMBO_BRAND", "PERSONAL_BRAND"}
ALLOWED_STATES = {
    "SOURCE_MATERIAL", "QUARANTINED", "CANDIDATE_SAFE",
    "READY_FOR_HUMAN_REVIEW", "PUBLISHED",
}
ALLOWED_CLAIMS = {"BUILT", "DEMO", "PILOT", "PRODUCTION", "MEASURED"}
RELEASEABLE_STATES = {"CANDIDATE_SAFE", "READY_FOR_HUMAN_REVIEW", "PUBLISHED"}
DEMO_LABEL = re.compile(r"\b(demo|simulad[oa]|example|ejemplo)\b", re.I)
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
        distribution = brand.load_distribution_lock(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return errors + [f"distribution authority invalid: {exc}"]
    distribution_status = distribution["overall_status"]

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
            else:
                identity_status, identity_reason = brand.admit_identity(identity, "PUBLIC_EXPRESSION", root)
                if identity_status != "PASS":
                    errors.append(f"{item_id}: identity is not admitted as PUBLIC_EXPRESSION ({identity_reason})")
        if lane == "PERSONAL_BRAND" and identity == "RUMBO IA":
            errors.append(f"{item_id}: personal lane cannot inherit RUMBO IA identity")

        copy = item.get("copy", "")
        if state in RELEASEABLE_STATES and (not isinstance(copy, str) or not copy.strip()):
            errors.append(f"{item_id}: releaseable state requires non-empty copy")
        if claim == "DEMO" and state in RELEASEABLE_STATES and isinstance(copy, str) and not DEMO_LABEL.search(copy):
            errors.append(f"{item_id}: DEMO releaseable copy requires visible demo/example label")
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
