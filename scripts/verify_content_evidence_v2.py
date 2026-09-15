from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
from datetime import datetime
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = pathlib.Path("docs/brand/content_registry_v2.json")
DISTRIBUTION_LOCK = pathlib.Path("docs/brand/distribution_lock_v1.json")
DECISION_SCHEMA = pathlib.Path("docs/brand/CONTENT_HUMAN_DECISION_OBSERVATION_SCHEMA_V1.json")
DECISION_LEDGER = pathlib.Path("docs/brand/content_human_decision_observations_v1.json")
OBSERVATION_SCHEMA = pathlib.Path("docs/brand/CONTENT_PUBLICATION_OBSERVATION_SCHEMA_V1.json")
OBSERVATION_LEDGER = pathlib.Path("docs/brand/content_publication_observations_v1.json")
PUBLICATION_V2_SCHEMA = pathlib.Path("docs/brand/CONTENT_PUBLICATION_RECEIPT_SCHEMA_V2.json")

HEX64 = re.compile(r"^[0-9a-f]{64}$")
CHANNEL_HOSTS = {
    "X": {"x.com", "www.x.com", "twitter.com", "www.twitter.com"},
    "LinkedIn": {"linkedin.com", "www.linkedin.com"},
}
AUTHORITY_CHAIN_STATE = "OBSERVED_REMOTE_EFFECT_OUTSIDE_COMPLETE_CANONICAL_AUTHORITY_CHAIN"


def _load(root: pathlib.Path, rel: pathlib.Path) -> dict:
    path = root / rel
    if not path.is_file():
        raise ValueError(f"missing required file: {rel.as_posix()}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _dt(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed


def _copy_sha(copy: str) -> str:
    return hashlib.sha256(copy.encode("utf-8")).hexdigest()


def _expected_identity(distribution: dict, channel: str) -> str | None:
    channels = distribution.get("channels", {})
    if channel == "X":
        handle = channels.get("x", {}).get("public_handle")
        return f"handle:{handle}" if isinstance(handle, str) and handle else None
    if channel == "LinkedIn":
        state = channels.get("linkedin", {})
        company_id = state.get("company_id")
        slug = state.get("public_slug")
        if isinstance(company_id, str) and company_id and isinstance(slug, str) and slug:
            return f"company:{company_id}:{slug}"
    return None


def _decision_errors(root: pathlib.Path, registry: dict) -> list[str]:
    errors: list[str] = []
    ledger = _load(root, DECISION_LEDGER)
    if ledger.get("schema_version") != 1 or not isinstance(ledger.get("observations"), list):
        return ["decision observation ledger malformed"]
    items = {item.get("id"): item for item in registry.get("items", []) if isinstance(item, dict)}
    seen: set[str] = set()
    for obs in ledger["observations"]:
        if not isinstance(obs, dict):
            errors.append("decision observation must be object")
            continue
        oid = obs.get("observation_id")
        if not isinstance(oid, str) or not oid or oid in seen:
            errors.append("decision observation_id must be unique non-empty string")
        else:
            seen.add(oid)
        if obs.get("decision_origin") != "human":
            errors.append(f"{oid}: decision_origin must be human")
        digest = obs.get("decision_text_sha256")
        if not isinstance(digest, str) or not HEX64.fullmatch(digest):
            errors.append(f"{oid}: decision_text_sha256 invalid")
        ids = obs.get("item_ids")
        channels = obs.get("target_channels")
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
            errors.append(f"{oid}: item_ids invalid")
            continue
        if not isinstance(channels, list) or not channels or len(channels) != len(set(channels)):
            errors.append(f"{oid}: target_channels invalid")
            continue
        for item_id in ids:
            item = items.get(item_id)
            if item is None:
                errors.append(f"{oid}: unknown item_id {item_id}")
                continue
            item_channels = set(item.get("target_channels", []))
            requested_channels = set(channels)
            decision_type = obs.get("decision_type")
            if decision_type == "EDITORIAL_APPROVAL":
                if requested_channels != item_channels:
                    errors.append(f"{oid}: target_channels mismatch for {item_id}")
            elif decision_type in {"AUTHORIZE_PUBLICATION", "AUTHORIZE_ONE_SHOT_AGENT_PUBLICATION_OVERRIDE"}:
                if not requested_channels.issubset(item_channels):
                    errors.append(f"{oid}: target_channels outside item scope for {item_id}")
            else:
                errors.append(f"{oid}: decision_type invalid")
        if obs.get("source_surface") != "chatgpt_chat":
            errors.append(f"{oid}: source_surface must be chatgpt_chat")
        signed = obs.get("human_signature_present")
        strength = obs.get("proof_strength")
        if signed is False and strength != "CHAT_OBSERVED_NOT_INDEPENDENTLY_SIGNED":
            errors.append(f"{oid}: unsigned observation must use chat-observed proof strength")
        if signed is True and strength != "HUMAN_SIGNED":
            errors.append(f"{oid}: signed observation must use HUMAN_SIGNED proof strength")
        try:
            _dt(obs.get("recorded_at"))
        except ValueError:
            errors.append(f"{oid}: recorded_at must be timezone-aware")
    return errors


def _observation_errors(root: pathlib.Path, registry: dict, distribution: dict) -> list[str]:
    errors: list[str] = []
    ledger = _load(root, OBSERVATION_LEDGER)
    observations = ledger.get("observations")
    if ledger.get("schema_version") != 1 or not isinstance(observations, list):
        return ["publication observation ledger malformed"]
    items = {item.get("id"): item for item in registry.get("items", []) if isinstance(item, dict)}
    pairs: set[tuple[str, str]] = set()
    remote_ids: set[str] = set()
    physical = 0
    for obs in observations:
        if not isinstance(obs, dict):
            errors.append("publication observation must be object")
            continue
        item_id = obs.get("item_id")
        channel = obs.get("channel")
        item = items.get(item_id)
        if item is None:
            errors.append(f"unknown observed item_id: {item_id}")
            continue
        pair = (item_id, channel)
        if pair in pairs:
            errors.append(f"duplicate item/channel observation: {item_id}/{channel}")
        pairs.add(pair)
        if channel not in item.get("target_channels", []):
            errors.append(f"{item_id}: observed channel not in target_channels: {channel}")
        copy = item.get("copy")
        if not isinstance(copy, str) or obs.get("content_sha256") != _copy_sha(copy):
            errors.append(f"{item_id}/{channel}: content_sha256 mismatch")
        expected_identity = _expected_identity(distribution, channel)
        if expected_identity is None or obs.get("account_identity") != expected_identity:
            errors.append(f"{item_id}/{channel}: account_identity mismatch")
        if obs.get("provider") != "Upload-Post":
            errors.append(f"{item_id}/{channel}: provider must be Upload-Post")
        for key in ("provider_request_id", "provider_job_id"):
            if not isinstance(obs.get(key), str) or not obs[key].strip():
                errors.append(f"{item_id}/{channel}: {key} required")
        if obs.get("account_binding_ref") != DISTRIBUTION_LOCK.as_posix():
            errors.append(f"{item_id}/{channel}: account_binding_ref mismatch")
        if obs.get("authority_chain_state") != AUTHORITY_CHAIN_STATE:
            errors.append(f"{item_id}/{channel}: authority_chain_state mismatch")
        if obs.get("canonical_promotion") != "NO_GO":
            errors.append(f"{item_id}/{channel}: observed effects must not self-promote")
        records = obs.get("remote_records")
        if not isinstance(records, list) or not records:
            errors.append(f"{item_id}/{channel}: remote_records required")
            continue
        root_count = 0
        for record in records:
            physical += 1
            if not isinstance(record, dict):
                errors.append(f"{item_id}/{channel}: remote record must be object")
                continue
            rid = record.get("remote_id")
            if not isinstance(rid, str) or not rid.strip():
                errors.append(f"{item_id}/{channel}: remote_id required")
            elif rid in remote_ids:
                errors.append(f"duplicate remote_id: {rid}")
            else:
                remote_ids.add(rid)
            if record.get("record_role") == "ROOT":
                root_count += 1
            elif record.get("record_role") != "ADDITIONAL_REMOTE_RECORD":
                errors.append(f"{item_id}/{channel}: invalid record_role")
            url = record.get("remote_url")
            host = (urlparse(url).hostname or "").lower() if isinstance(url, str) else ""
            if host not in CHANNEL_HOSTS.get(channel, set()):
                errors.append(f"{item_id}/{channel}: remote_url host mismatch")
            try:
                published_at = _dt(record.get("published_at"))
                readback_at = _dt(record.get("readback_at"))
                if readback_at < published_at:
                    errors.append(f"{item_id}/{channel}: readback precedes publish")
            except ValueError:
                errors.append(f"{item_id}/{channel}: timestamps must be timezone-aware")
            if record.get("readback_status") != "PASS":
                errors.append(f"{item_id}/{channel}: readback_status must be PASS")
        if root_count != 1:
            errors.append(f"{item_id}/{channel}: exactly one ROOT remote record required")
    coverage = ledger.get("coverage", {})
    if coverage.get("logical_targets_observed") != len(pairs):
        errors.append("coverage logical_targets_observed mismatch")
    if coverage.get("physical_remote_records") != physical:
        errors.append("coverage physical_remote_records mismatch")
    if ledger.get("invariant") != "OBSERVED_REMOTE_EFFECT_DOES_NOT_IMPLY_CANONICAL_PUBLISHED":
        errors.append("observation ledger invariant missing")
    return errors


def _schema_errors(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    for rel in (DECISION_SCHEMA, OBSERVATION_SCHEMA, PUBLICATION_V2_SCHEMA):
        try:
            _load(root, rel)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
    try:
        schema = _load(root, PUBLICATION_V2_SCHEMA)
        if schema.get("properties", {}).get("schema_version", {}).get("const") != 2:
            errors.append("publication receipt V2 schema_version must be 2")
        defs = schema.get("$defs", {})
        channel_pub = defs.get("channel_publication", {})
        required = set(channel_pub.get("required", []))
        for key in ("provider_request_id", "provider_job_id", "remote_records"):
            if key not in required:
                errors.append(f"publication receipt V2 must require {key}")
        remote_record = defs.get("remote_record", {})
        if "record_role" not in set(remote_record.get("required", [])):
            errors.append("publication receipt V2 must require record_role")
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    return errors


def verify(root: pathlib.Path = ROOT) -> list[str]:
    errors = _schema_errors(root)
    try:
        registry = _load(root, REGISTRY)
        policy = registry.get("evidence_observation_policy")
        expected_policy = {
            "decision_observation_schema_ref": DECISION_SCHEMA.as_posix(),
            "decision_observation_ledger_ref": DECISION_LEDGER.as_posix(),
            "publication_observation_schema_ref": OBSERVATION_SCHEMA.as_posix(),
            "publication_observation_ledger_ref": OBSERVATION_LEDGER.as_posix(),
            "publication_receipt_v2_schema_ref": PUBLICATION_V2_SCHEMA.as_posix(),
            "observations_grant_authority": False,
            "observations_promote_state": False,
        }
        if policy != expected_policy:
            errors.append("evidence_observation_policy must remain fail-closed")
        distribution = _load(root, DISTRIBUTION_LOCK)
        if distribution.get("overall_status") != "PASS":
            errors.append("distribution lock must remain PASS")
        errors.extend(_decision_errors(root, registry))
        errors.extend(_observation_errors(root, registry, distribution))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    return errors


def main() -> int:
    errors = verify(ROOT)
    if errors:
        print("CONTENT_EVIDENCE_V2_FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("CONTENT_EVIDENCE_V2_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
