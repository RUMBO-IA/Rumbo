from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from datetime import datetime

try:
    from scripts import verify_brand_contract as brand
except ImportError:  # direct execution: python scripts/verify_content_contract.py
    import verify_brand_contract as brand

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = pathlib.Path("docs/brand/content_registry_v2.json")
DISTRIBUTION_LOCK = pathlib.Path("docs/brand/distribution_lock_v1.json")
CANON = pathlib.Path("docs/brand/CONTENT_CANON_V2.md")
CHANNEL_MATRIX = pathlib.Path("docs/brand/CHANNEL_MATRIX_V1.md")
APPROVAL_SCHEMA = pathlib.Path("docs/brand/CONTENT_APPROVAL_RECEIPT_SCHEMA_V1.json")
APPROVAL_DIR = pathlib.Path("docs/brand/content_approval_receipts")

EXPECTED_DOMAIN = "https://rumbo.verso.fans"
ALLOWED_LANES = {"RUMBO_BRAND", "PERSONAL_BRAND"}
ALLOWED_STATES = {
    "SOURCE_MATERIAL", "QUARANTINED", "CANDIDATE_SAFE",
    "READY_FOR_HUMAN_REVIEW", "APPROVED", "PUBLISHED",
}
ALLOWED_CLAIMS = {"BUILT", "DEMO", "PILOT", "PRODUCTION", "MEASURED"}
RELEASEABLE_STATES = {"CANDIDATE_SAFE", "READY_FOR_HUMAN_REVIEW", "APPROVED", "PUBLISHED"}
REVIEW_CHAIN_STATES = {"READY_FOR_HUMAN_REVIEW", "APPROVED", "PUBLISHED"}
APPROVAL_REQUIRED_STATES = {"APPROVED", "PUBLISHED"}
REQUIRED_APPROVAL_SOURCE = "explicit_human_approval"
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


def _copy_sha256(copy: str) -> str:
    return hashlib.sha256(copy.encode("utf-8")).hexdigest()


def _approval_receipt_errors(root: pathlib.Path, item: dict, item_id: str, copy: str, channels: list[str]) -> list[str]:
    errors: list[str] = []
    receipt_ref = item.get("approval_receipt_ref")
    if not isinstance(receipt_ref, str) or not receipt_ref.strip():
        return [f"{item_id}: approval state requires approval_receipt_ref"]

    rel = pathlib.Path(receipt_ref)
    if rel.is_absolute() or ".." in rel.parts or rel.suffix.lower() != ".json":
        return [f"{item_id}: approval_receipt_ref must be a JSON file under {APPROVAL_DIR.as_posix()}"]
    expected_prefix = APPROVAL_DIR.parts
    if rel.parts[:len(expected_prefix)] != expected_prefix:
        return [f"{item_id}: approval_receipt_ref must be under {APPROVAL_DIR.as_posix()}"]

    try:
        receipt = _load_json(root, rel)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"{item_id}: approval receipt invalid: {exc}"]

    if receipt.get("schema_version") != 1:
        errors.append(f"{item_id}: approval receipt schema_version must be 1")
    if receipt.get("item_id") != item_id:
        errors.append(f"{item_id}: approval receipt item_id mismatch")
    if receipt.get("decision") != "APPROVED":
        errors.append(f"{item_id}: approval receipt decision must be APPROVED")
    if receipt.get("content_sha256") != _copy_sha256(copy):
        errors.append(f"{item_id}: approval receipt content_sha256 mismatch")
    if receipt.get("review_packet_ref") != item.get("review_packet_ref"):
        errors.append(f"{item_id}: approval receipt review_packet_ref mismatch")

    receipt_channels = receipt.get("target_channels")
    if not isinstance(receipt_channels, list) or len(receipt_channels) != len(set(receipt_channels)) or set(receipt_channels) != set(channels):
        errors.append(f"{item_id}: approval receipt target_channels mismatch")

    if not isinstance(receipt.get("reviewer"), str) or not receipt["reviewer"].strip():
        errors.append(f"{item_id}: approval receipt reviewer required")
    if receipt.get("source") != REQUIRED_APPROVAL_SOURCE:
        errors.append(f"{item_id}: approval receipt source must be {REQUIRED_APPROVAL_SOURCE}")

    reviewed_at = receipt.get("reviewed_at")
    try:
        parsed = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00")) if isinstance(reviewed_at, str) else None
        if parsed is None or parsed.tzinfo is None:
            raise ValueError("timezone required")
    except ValueError:
        errors.append(f"{item_id}: approval receipt reviewed_at must be timezone-aware ISO-8601")
    return errors



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
    if not (root / APPROVAL_SCHEMA).is_file():
        errors.append("content approval receipt schema missing")
    approval_policy = data.get("approval_policy")
    expected_policy = {
        "receipt_schema_ref": APPROVAL_SCHEMA.as_posix(),
        "receipt_directory": APPROVAL_DIR.as_posix(),
        "required_source": REQUIRED_APPROVAL_SOURCE,
        "agent_may_issue_receipts": False,
    }
    if approval_policy != expected_policy:
        errors.append("approval_policy must remain fail-closed and forbid agent-issued receipts")

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

        if state in REVIEW_CHAIN_STATES and not evidence:
            errors.append(f"{item_id}: review-chain item requires evidence")
        channels: list[str] = []
        if state in REVIEW_CHAIN_STATES:
            packet_ref = item.get("review_packet_ref")
            if not isinstance(packet_ref, str) or not packet_ref.strip():
                errors.append(f"{item_id}: review-chain item requires review_packet_ref")
            else:
                packet_path = root / packet_ref
                if not packet_path.is_file():
                    errors.append(f"{item_id}: review_packet_ref missing")
                else:
                    packet_text = packet_path.read_text(encoding="utf-8-sig")
                    if item_id not in packet_text or (isinstance(copy, str) and copy.strip() not in packet_text):
                        errors.append(f"{item_id}: review packet must contain exact id and copy")
            raw_channels = item.get("target_channels")
            if not isinstance(raw_channels, list) or not raw_channels or not all(isinstance(ch, str) and ch.strip() for ch in raw_channels):
                errors.append(f"{item_id}: review-chain item requires target_channels")
            else:
                channels = raw_channels
                matrix_path = root / CHANNEL_MATRIX
                if not matrix_path.is_file():
                    errors.append(f"{item_id}: channel matrix missing")
                else:
                    matrix_text = matrix_path.read_text(encoding="utf-8-sig")
                    for channel in channels:
                        if f"| {channel} |" not in matrix_text:
                            errors.append(f"{item_id}: target channel not in CHANNEL_MATRIX_V1: {channel}")
        if state in REVIEW_CHAIN_STATES and distribution_status != "PASS":
            errors.append(f"{item_id}: release state requires DISTRIBUTION=PASS")
        if claim == "MEASURED" and state not in {"QUARANTINED", "SOURCE_MATERIAL"}:
            if not item.get("metric_receipt"):
                errors.append(f"{item_id}: MEASURED claim requires metric_receipt")
        if state in APPROVAL_REQUIRED_STATES and isinstance(copy, str) and copy.strip() and channels:
            errors.extend(_approval_receipt_errors(root, item, item_id, copy, channels))
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
