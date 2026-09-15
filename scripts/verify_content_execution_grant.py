from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
BRAND = pathlib.Path("docs/brand")
POLICY = BRAND / "CONTENT_EXECUTION_GRANT_POLICY_V1.json"
SCHEMA = BRAND / "CONTENT_EXECUTION_GRANT_SCHEMA_V1.json"
GRANTS = BRAND / "content_execution_grants_v1.json"
REGISTRY = BRAND / "content_registry_v2.json"
DECISIONS = BRAND / "content_human_decision_observations_v1.json"
OBSERVATIONS = BRAND / "content_publication_observations_v1.json"
DISTRIBUTION = BRAND / "distribution_lock_v1.json"
TERMINAL = {"CONSUMED", "REVOKED", "EXPIRED"}
ISSUANCE_FIELDS = (
    "schema_version",
    "grant_id",
    "mode",
    "authority_anchor_commit",
    "publication_decision_observation_id",
    "override_decision_observation_id",
    "item_allowlist",
    "channel_allowlist",
    "account_identity",
    "scope_sha256",
    "original_logical_target_limit",
    "observed_logical_targets_before_grant",
    "remaining_logical_target_limit",
    "base_agent_may_publish",
    "standing_permission",
    "auto_publish",
    "revocation_required",
    "effective_ref",
    "granted_at",
    "expires_at",
    "source",
)


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


def _scope_sha(grant: dict) -> str:
    scope = {
        "item_allowlist": grant.get("item_allowlist"),
        "channel_allowlist": grant.get("channel_allowlist"),
        "account_identity": grant.get("account_identity"),
        "remaining_logical_target_limit": grant.get("remaining_logical_target_limit"),
    }
    raw = json.dumps(scope, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _issuance_state_sha(grant: dict) -> str:
    state = {field: grant.get(field) for field in ISSUANCE_FIELDS}
    raw = json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _git_json(root: pathlib.Path, rev: str, rel: pathlib.Path, *, required: bool = False) -> dict | None:
    if not (root / ".git").exists():
        return None
    proc = subprocess.run(
        ["git", "-C", str(root), "show", f"{rev}:{rel.as_posix()}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        if required:
            raise ValueError(f"required git object unreadable: {rev}:{rel.as_posix()}")
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        if required:
            raise ValueError(f"required git object is not valid JSON: {rev}:{rel.as_posix()}") from exc
        raise


def _approved_targets(registry: dict) -> set[tuple[str, str]]:
    items = {i.get("id"): i for i in registry.get("items", []) if isinstance(i, dict)}
    approved = {k: v for k, v in items.items() if v.get("publication_state") == "APPROVED"}
    return {(item_id, ch) for item_id, item in approved.items() for ch in item.get("target_channels", [])}


def _observed_pairs(observations: dict) -> set[tuple[str, str]]:
    return {
        (o.get("item_id"), o.get("channel"))
        for o in observations.get("observations", [])
        if isinstance(o, dict)
    }


def verify(root: pathlib.Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        policy = _load(root, POLICY)
        schema = _load(root, SCHEMA)
        ledger = _load(root, GRANTS)
        registry = _load(root, REGISTRY)
        decisions = _load(root, DECISIONS)
        observations = _load(root, OBSERVATIONS)
        distribution = _load(root, DISTRIBUTION)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    expected_policy = {
        "schema_version": 1,
        "base_agent_may_publish": False,
        "one_shot_scoped_grants_allowed": True,
        "grant_schema_ref": SCHEMA.as_posix(),
        "grant_ledger_ref": GRANTS.as_posix(),
        "authority_observation_ledger_ref": DECISIONS.as_posix(),
        "authority_anchor_commit": "377a7105dc929b0195c149b5702ac174fbabf5de",
        "grant_issuance_commit": "cec887029a78974f23e530772e3bb46b2054ae02",
        "grant_issuance_state_sha256": "3484247f05ffede2bd463b4521d67b061781d5601b731f0fbc715e9049b82ba2",
        "required_publication_decision_type": "AUTHORIZE_PUBLICATION",
        "required_override_decision_type": "AUTHORIZE_ONE_SHOT_AGENT_PUBLICATION_OVERRIDE",
        "observations_alone_grant_authority": False,
        "grant_effective_only_when_present_on_main": True,
        "grant_scope_must_equal_unobserved_approved_targets_at_issuance": True,
        "terminal_grant_scope_is_immutable_issuance_snapshot": True,
        "standing_permission": False,
        "auto_publish": "NO_GO",
        "terminal_statuses": ["CONSUMED", "REVOKED", "EXPIRED"],
        "terminal_grants_execute": False,
        "terminal_transition_requires_timestamp_and_reason": True,
        "terminal_status_is_irreversible": True,
    }
    if policy != expected_policy:
        errors.append("execution grant policy must remain exact and fail-closed")

    props = schema.get("properties", {})
    if props.get("mode", {}).get("const") != "ONE_SHOT":
        errors.append("grant schema must remain ONE_SHOT")
    if props.get("scoped_agent_execution_authorized", {}).get("type") != "boolean":
        errors.append("grant schema execution flag must be boolean")
    if props.get("item_allowlist", {}).get("minItems") != 1:
        errors.append("grant schema must preserve non-empty issuance scope")
    if props.get("remaining_logical_target_limit", {}).get("minimum") != 1:
        errors.append("grant schema must preserve positive issuance remaining limit")

    grants = ledger.get("grants")
    if ledger.get("schema_version") != 1 or not isinstance(grants, list) or len(grants) != 1:
        return errors + ["grant ledger must contain exactly one governed grant"]
    grant = grants[0]
    status = grant.get("status")
    if status not in {"ACTIVE", *TERMINAL}:
        errors.append("unknown grant lifecycle status")

    if grant.get("mode") != "ONE_SHOT":
        errors.append("execution grant must remain ONE_SHOT")
    if grant.get("authority_anchor_commit") != policy.get("authority_anchor_commit"):
        errors.append("grant authority anchor mismatch")
    if _issuance_state_sha(grant) != policy.get("grant_issuance_state_sha256"):
        errors.append("grant issuance snapshot differs from pinned issuance state")
    if grant.get("base_agent_may_publish") is not False:
        errors.append("base agent permission must remain false")
    if grant.get("standing_permission") is not False:
        errors.append("standing permission must remain false")
    if grant.get("auto_publish") != "NO_GO":
        errors.append("AUTO_PUBLISH must remain NO_GO")
    if grant.get("revocation_required") is not True:
        errors.append("grant must require revocation")
    if grant.get("effective_ref") != "refs/heads/main":
        errors.append("grant effective_ref must be main")
    if grant.get("source") != "derived_from_preexisting_human_decision_observations":
        errors.append("grant source invalid")
    if grant.get("scope_sha256") != _scope_sha(grant):
        errors.append("grant scope_sha256 mismatch")

    try:
        granted_at = _dt(grant.get("granted_at"))
        expires_at = _dt(grant.get("expires_at"))
        if expires_at <= granted_at:
            errors.append("grant expiry must follow grant time")
    except ValueError:
        granted_at = expires_at = None
        errors.append("grant timestamps must be timezone-aware")

    all_targets = _approved_targets(registry)
    observed_pairs = _observed_pairs(observations)
    missing = all_targets - observed_pairs
    grant_pairs = {
        (item_id, ch)
        for item_id in grant.get("item_allowlist", [])
        for ch in grant.get("channel_allowlist", [])
    }
    if status == "ACTIVE":
        if grant_pairs != missing:
            errors.append("ACTIVE grant scope must equal exact current unobserved approved targets")
    elif not missing.issubset(grant_pairs):
        errors.append("current unobserved target lies outside immutable issuance scope")

    now = datetime.now(timezone.utc)
    execution_flag = grant.get("scoped_agent_execution_authorized")
    if status == "ACTIVE":
        if execution_flag is not True:
            errors.append("ACTIVE grant must authorize scoped execution")
        if expires_at is not None and now >= expires_at.astimezone(timezone.utc):
            errors.append("ACTIVE execution grant is expired")
        if grant.get("status_changed_at") is not None or grant.get("status_reason") is not None:
            errors.append("ACTIVE grant must not carry terminal status metadata")
        if not missing:
            errors.append("ACTIVE grant cannot remain live after scope exhaustion")
    else:
        if execution_flag is not False:
            errors.append("terminal grant must not authorize execution")
        try:
            changed_at = _dt(grant.get("status_changed_at"))
            if granted_at is not None and changed_at < granted_at:
                errors.append("terminal status cannot predate grant")
        except ValueError:
            errors.append("terminal grant requires timezone-aware status_changed_at")
        if not isinstance(grant.get("status_reason"), str) or not grant["status_reason"].strip():
            errors.append("terminal grant requires status_reason")
        if status == "EXPIRED" and expires_at is not None:
            expiry_utc = expires_at.astimezone(timezone.utc)
            if now < expiry_utc:
                errors.append("EXPIRED grant cannot precede expires_at")
            if "changed_at" in locals() and changed_at.astimezone(timezone.utc) < expiry_utc:
                errors.append("EXPIRED status_changed_at cannot predate expires_at")
        if status == "CONSUMED" and missing:
            errors.append("CONSUMED grant requires zero current missing targets")

    linkedin = distribution.get("channels", {}).get("linkedin", {})
    expected_identity = f"company:{linkedin.get('company_id')}:{linkedin.get('public_slug')}"
    if grant.get("account_identity") != expected_identity:
        errors.append("grant account identity mismatch")
    if set(grant.get("channel_allowlist", [])) != {"LinkedIn"}:
        errors.append("grant issuance scope may reference LinkedIn only")

    decision_map = {
        o.get("observation_id"): o
        for o in decisions.get("observations", [])
        if isinstance(o, dict)
    }
    pub = decision_map.get(grant.get("publication_decision_observation_id"))
    override = decision_map.get(grant.get("override_decision_observation_id"))
    if not pub or pub.get("decision_type") != policy.get("required_publication_decision_type"):
        errors.append("publication decision observation missing or wrong type")
    if not override or override.get("decision_type") != policy.get("required_override_decision_type"):
        errors.append("one-shot override observation missing or wrong type")
    for name, obs in (("publication", pub), ("override", override)):
        if not obs:
            continue
        if obs.get("decision_origin") != "human" or obs.get("source_surface") != "chatgpt_chat":
            errors.append(f"{name} decision provenance invalid")
        if obs.get("proof_strength") != "CHAT_OBSERVED_NOT_INDEPENDENTLY_SIGNED" or obs.get("human_signature_present") is not False:
            errors.append(f"{name} decision proof classification changed")
        if not set(grant.get("item_allowlist", [])).issubset(set(obs.get("item_ids", []))):
            errors.append(f"{name} decision does not cover all grant items")
        if not set(grant.get("channel_allowlist", [])).issubset(set(obs.get("target_channels", []))):
            errors.append(f"{name} decision does not cover all grant channels")

    try:
        anchored = _git_json(
            root,
            policy["authority_anchor_commit"],
            DECISIONS,
            required=True,
        )
        if anchored is not None:
            anchor_map = {
                o.get("observation_id"): o
                for o in anchored.get("observations", [])
                if isinstance(o, dict)
            }
            for obs_id in (
                grant.get("publication_decision_observation_id"),
                grant.get("override_decision_observation_id"),
            ):
                if anchor_map.get(obs_id) != decision_map.get(obs_id):
                    errors.append(f"decision observation not identical to authority anchor: {obs_id}")

        issuance_ledger = _git_json(
            root,
            policy["grant_issuance_commit"],
            GRANTS,
            required=True,
        )
        issuance_registry = _git_json(
            root,
            policy["grant_issuance_commit"],
            REGISTRY,
            required=True,
        )
        issuance_observations = _git_json(
            root,
            policy["grant_issuance_commit"],
            OBSERVATIONS,
            required=True,
        )
        if issuance_ledger is not None and issuance_registry is not None and issuance_observations is not None:
            issuance_grants = issuance_ledger.get("grants", [])
            if len(issuance_grants) != 1:
                errors.append("issuance commit must contain exactly one governed grant")
            else:
                issuance_grant = issuance_grants[0]
                if issuance_grant.get("grant_id") != grant.get("grant_id"):
                    errors.append("issuance grant identity mismatch")
                if _issuance_state_sha(issuance_grant) != policy.get("grant_issuance_state_sha256"):
                    errors.append("pinned issuance commit does not match issuance-state digest")
                issuance_targets = _approved_targets(issuance_registry)
                issuance_observed = _observed_pairs(issuance_observations)
                issuance_missing = issuance_targets - issuance_observed
                issuance_pairs = {
                    (item_id, ch)
                    for item_id in issuance_grant.get("item_allowlist", [])
                    for ch in issuance_grant.get("channel_allowlist", [])
                }
                if issuance_pairs != issuance_missing:
                    errors.append("issuance grant scope was not exact unobserved approved targets")
                if issuance_grant.get("original_logical_target_limit") != len(issuance_targets):
                    errors.append("issuance original logical target limit mismatch")
                if issuance_grant.get("observed_logical_targets_before_grant") != len(issuance_observed):
                    errors.append("issuance observed-before-grant count mismatch")
                if issuance_grant.get("remaining_logical_target_limit") != len(issuance_missing):
                    errors.append("issuance remaining logical target limit mismatch")

        previous = _git_json(root, "HEAD^", GRANTS)
        if previous and previous.get("grants"):
            prior = previous["grants"][0]
            if (
                prior.get("grant_id") == grant.get("grant_id")
                and prior.get("status") in TERMINAL
                and status != prior.get("status")
            ):
                errors.append("terminal grant lifecycle is irreversible")
    except (ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))

    return errors


def main() -> int:
    if not (ROOT / ".git").exists():
        print("CONTENT_EXECUTION_GRANT_FAIL")
        print("- repository git metadata is required for authority verification")
        return 1
    errors = verify(ROOT)
    if errors:
        print("CONTENT_EXECUTION_GRANT_FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("CONTENT_EXECUTION_GRANT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
