from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

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
PUBLICATION_SCHEMA = pathlib.Path("docs/brand/CONTENT_PUBLICATION_RECEIPT_SCHEMA_V1.json")
PUBLICATION_DIR = pathlib.Path("docs/brand/content_publication_receipts")
PUBLICATION_AUTH_SCHEMA = pathlib.Path("docs/brand/CONTENT_PUBLICATION_AUTHORIZATION_RECEIPT_SCHEMA_V1.json")
PUBLICATION_AUTH_DIR = pathlib.Path("docs/brand/content_publication_authorization_receipts")

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
REQUIRED_PUBLICATION_SOURCE = "authenticated_publication_action"
REQUIRED_PUBLICATION_AUTH_SOURCE = "explicit_human_publication_authorization"
REQUIRED_READBACK_STATUS = "PASS"
CHANNEL_HOSTS = {
    "LinkedIn": {"linkedin.com", "www.linkedin.com"},
    "X": {"x.com", "www.x.com", "twitter.com", "www.twitter.com"},
    "YouTube": {"youtube.com", "www.youtube.com", "youtu.be"},
    "Website": {"rumbo.verso.fans"},
    "GitHub org": {"github.com", "www.github.com"},
}
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
    valid_receipt_channels = isinstance(receipt_channels, list) and all(isinstance(ch, str) and ch.strip() for ch in receipt_channels)
    if not valid_receipt_channels or len(receipt_channels) != len(set(receipt_channels)) or set(receipt_channels) != set(channels):
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


def _distribution_lock_sha256(root: pathlib.Path) -> str:
    data = _load_json(root, DISTRIBUTION_LOCK)
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _expected_account_identity(distribution: dict, channel: str) -> str | None:
    states = distribution.get("channels", {})
    if channel == "X":
        handle = states.get("x", {}).get("public_handle")
        return f"handle:{handle}" if isinstance(handle, str) and handle.strip() else None
    if channel == "LinkedIn":
        state = states.get("linkedin", {})
        company_id = state.get("company_id")
        slug = state.get("public_slug")
        if isinstance(company_id, str) and company_id.strip() and isinstance(slug, str) and slug.strip():
            return f"company:{company_id}:{slug}"
        return None
    if channel == "YouTube":
        handle = states.get("youtube", {}).get("public_handle")
        return f"handle:{handle}" if isinstance(handle, str) and handle.strip() else None
    if channel == "Website":
        return "domain:rumbo.verso.fans"
    return None


def _publication_authorization_errors(root: pathlib.Path, item: dict, item_id: str, copy: str, channels: list[str]) -> list[str]:
    errors: list[str] = []
    receipt_ref = item.get("publication_authorization_receipt_ref")
    if not isinstance(receipt_ref, str) or not receipt_ref.strip():
        return [f"{item_id}: PUBLISHED requires publication_authorization_receipt_ref"]
    rel = pathlib.Path(receipt_ref)
    if rel.is_absolute() or ".." in rel.parts or rel.suffix.lower() != ".json" or rel.parts[:len(PUBLICATION_AUTH_DIR.parts)] != PUBLICATION_AUTH_DIR.parts:
        return [f"{item_id}: publication_authorization_receipt_ref must be a JSON file under {PUBLICATION_AUTH_DIR.as_posix()}"]
    try:
        receipt = _load_json(root, rel)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"{item_id}: publication authorization invalid: {exc}"]
    allowed = {"schema_version","item_id","decision","content_sha256","approval_receipt_ref","target_channels","authorizer","authorized_at","source","notes"}
    if set(receipt) - allowed: errors.append(f"{item_id}: publication authorization contains unsupported fields")
    if receipt.get("schema_version") != 1: errors.append(f"{item_id}: publication authorization schema_version must be 1")
    if receipt.get("item_id") != item_id: errors.append(f"{item_id}: publication authorization item_id mismatch")
    if receipt.get("decision") != "AUTHORIZE_PUBLICATION": errors.append(f"{item_id}: publication authorization decision must be AUTHORIZE_PUBLICATION")
    if receipt.get("content_sha256") != _copy_sha256(copy): errors.append(f"{item_id}: publication authorization content_sha256 mismatch")
    if receipt.get("approval_receipt_ref") != item.get("approval_receipt_ref"): errors.append(f"{item_id}: publication authorization approval_receipt_ref mismatch")
    rc = receipt.get("target_channels")
    valid_rc = isinstance(rc, list) and all(isinstance(ch, str) and ch.strip() for ch in rc)
    if not valid_rc or len(rc) != len(set(rc)) or set(rc) != set(channels): errors.append(f"{item_id}: publication authorization target_channels mismatch")
    if not isinstance(receipt.get("authorizer"), str) or not receipt["authorizer"].strip(): errors.append(f"{item_id}: publication authorization authorizer required")
    if receipt.get("source") != REQUIRED_PUBLICATION_AUTH_SOURCE: errors.append(f"{item_id}: publication authorization source must be {REQUIRED_PUBLICATION_AUTH_SOURCE}")
    value = receipt.get("authorized_at")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else None
        if parsed is None or parsed.tzinfo is None: raise ValueError("timezone required")
    except ValueError:
        errors.append(f"{item_id}: publication authorization authorized_at must be timezone-aware ISO-8601")
    return errors


def _publication_receipt_errors(root: pathlib.Path, item: dict, item_id: str, copy: str, channels: list[str], distribution: dict) -> list[str]:
    errors: list[str] = []
    receipt_ref = item.get("publication_receipt")
    if not isinstance(receipt_ref, str) or not receipt_ref.strip():
        return [f"{item_id}: PUBLISHED requires publication_receipt"]

    rel = pathlib.Path(receipt_ref)
    if rel.is_absolute() or ".." in rel.parts or rel.suffix.lower() != ".json":
        return [f"{item_id}: publication_receipt must be a JSON file under {PUBLICATION_DIR.as_posix()}"]
    expected_prefix = PUBLICATION_DIR.parts
    if rel.parts[:len(expected_prefix)] != expected_prefix:
        return [f"{item_id}: publication_receipt must be under {PUBLICATION_DIR.as_posix()}"]

    try:
        receipt = _load_json(root, rel)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"{item_id}: publication receipt invalid: {exc}"]

    if receipt.get("schema_version") != 1:
        errors.append(f"{item_id}: publication receipt schema_version must be 1")
    if receipt.get("item_id") != item_id:
        errors.append(f"{item_id}: publication receipt item_id mismatch")
    if receipt.get("status") != "PUBLISHED":
        errors.append(f"{item_id}: publication receipt status must be PUBLISHED")
    if receipt.get("content_sha256") != _copy_sha256(copy):
        errors.append(f"{item_id}: publication receipt content_sha256 mismatch")
    if receipt.get("distribution_lock_sha256") != _distribution_lock_sha256(root):
        errors.append(f"{item_id}: publication receipt distribution_lock_sha256 mismatch")
    if receipt.get("approval_receipt_ref") != item.get("approval_receipt_ref"):
        errors.append(f"{item_id}: publication receipt approval_receipt_ref mismatch")
    if receipt.get("publication_authorization_receipt_ref") != item.get("publication_authorization_receipt_ref"):
        errors.append(f"{item_id}: publication receipt publication_authorization_receipt_ref mismatch")
    if receipt.get("review_packet_ref") != item.get("review_packet_ref"):
        errors.append(f"{item_id}: publication receipt review_packet_ref mismatch")

    allowed_receipt_keys = {"schema_version", "item_id", "status", "content_sha256", "distribution_lock_sha256", "approval_receipt_ref", "publication_authorization_receipt_ref", "review_packet_ref", "target_channels", "publications", "publisher", "source", "notes"}
    if set(receipt) - allowed_receipt_keys:
        errors.append(f"{item_id}: publication receipt contains unsupported fields")
    receipt_channels = receipt.get("target_channels")
    valid_receipt_channels = isinstance(receipt_channels, list) and all(isinstance(ch, str) and ch.strip() for ch in receipt_channels)
    if not valid_receipt_channels or len(receipt_channels) != len(set(receipt_channels)) or set(receipt_channels) != set(channels):
        errors.append(f"{item_id}: publication receipt target_channels mismatch")
    if not isinstance(receipt.get("publisher"), str) or not receipt["publisher"].strip():
        errors.append(f"{item_id}: publication receipt publisher required")
    if receipt.get("source") != REQUIRED_PUBLICATION_SOURCE:
        errors.append(f"{item_id}: publication receipt source must be {REQUIRED_PUBLICATION_SOURCE}")

    publications = receipt.get("publications")
    if not isinstance(publications, list) or not publications:
        errors.append(f"{item_id}: publication receipt publications required")
        return errors
    seen: set[str] = set()
    for pub in publications:
        if not isinstance(pub, dict):
            errors.append(f"{item_id}: publication entry must be an object")
            continue
        allowed_pub_keys = {"channel", "account_identity", "remote_url", "remote_id", "published_at", "readback_at", "readback_status", "account_binding_ref"}
        if set(pub) - allowed_pub_keys:
            errors.append(f"{item_id}: publication entry contains unsupported fields")
        channel = pub.get("channel")
        if not isinstance(channel, str) or not channel.strip():
            errors.append(f"{item_id}: publication channel required")
            continue
        if channel in seen:
            errors.append(f"{item_id}: duplicate publication channel: {channel}")
        seen.add(channel)

        if channel not in channels:
            errors.append(f"{item_id}: publication channel not in target_channels: {channel}")
        expected_identity = _expected_account_identity(distribution, channel)
        if expected_identity is None:
            errors.append(f"{item_id}: publication account identity policy missing for channel: {channel}")
        elif pub.get("account_identity") != expected_identity:
            errors.append(f"{item_id}: publication account_identity mismatch for {channel}")
        remote_url = pub.get("remote_url")
        if not isinstance(remote_url, str) or not re.match(r"^https?://", remote_url):
            errors.append(f"{item_id}: publication remote_url must be http(s)")
        else:
            host = (urlparse(remote_url).hostname or "").lower()
            allowed_hosts = CHANNEL_HOSTS.get(channel)
            if allowed_hosts is None:
                errors.append(f"{item_id}: publication host policy missing for channel: {channel}")
            elif host not in allowed_hosts:
                errors.append(f"{item_id}: publication remote_url host mismatch for {channel}: {host}")
            elif channel == "X" and expected_identity is not None:
                expected_handle = expected_identity.split(":", 1)[1].casefold()
                path_parts = [part for part in urlparse(remote_url).path.split("/") if part]
                if not path_parts or path_parts[0].lstrip("@").casefold() != expected_handle:
                    errors.append(f"{item_id}: publication X URL does not bind canonical handle")
        if not isinstance(pub.get("remote_id"), str) or not pub["remote_id"].strip():
            errors.append(f"{item_id}: publication remote_id required")
        if pub.get("account_binding_ref") != DISTRIBUTION_LOCK.as_posix():
            errors.append(f"{item_id}: publication account_binding_ref mismatch")
        if pub.get("readback_status") != REQUIRED_READBACK_STATUS:
            errors.append(f"{item_id}: publication readback_status must be PASS")

        parsed_times = {}
        for field in ("published_at", "readback_at"):
            value = pub.get(field)
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else None
                if parsed is None or parsed.tzinfo is None:
                    raise ValueError("timezone required")
                parsed_times[field] = parsed
            except ValueError:
                errors.append(f"{item_id}: publication {field} must be timezone-aware ISO-8601")
        if set(parsed_times) == {"published_at", "readback_at"} and parsed_times["readback_at"] < parsed_times["published_at"]:
            errors.append(f"{item_id}: publication readback_at precedes published_at")

    if seen != set(channels):
        errors.append(f"{item_id}: publication entries must match target_channels exactly")
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
    if not (root / PUBLICATION_SCHEMA).is_file():
        errors.append("content publication receipt schema missing")
    if not (root / PUBLICATION_AUTH_SCHEMA).is_file():
        errors.append("content publication authorization schema missing")
    publication_policy = data.get("publication_policy")
    expected_publication_policy = {
        "receipt_schema_ref": PUBLICATION_SCHEMA.as_posix(),
        "receipt_directory": PUBLICATION_DIR.as_posix(),
        "required_source": REQUIRED_PUBLICATION_SOURCE,
        "required_readback_status": REQUIRED_READBACK_STATUS,
        "agent_may_publish": False,
        "bind_current_distribution_lock_sha256": True,
        "authorization_schema_ref": PUBLICATION_AUTH_SCHEMA.as_posix(),
        "authorization_directory": PUBLICATION_AUTH_DIR.as_posix(),
        "required_authorization_source": REQUIRED_PUBLICATION_AUTH_SOURCE,
    }
    if publication_policy != expected_publication_policy:
        errors.append("publication_policy must remain fail-closed and forbid agent publication")

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
        if state == "PUBLISHED" and isinstance(copy, str) and copy.strip() and channels:
            errors.extend(_publication_authorization_errors(root, item, item_id, copy, channels))
            errors.extend(_publication_receipt_errors(root, item, item_id, copy, channels, distribution))

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
