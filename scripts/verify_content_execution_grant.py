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


def _anchor_decisions(root: pathlib.Path, commit: str) -> dict | None:
    if not (root / ".git").exists():
        return None
    proc = subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{DECISIONS.as_posix()}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if proc.returncode != 0:
        raise ValueError("authority anchor commit cannot read decision ledger")
    return json.loads(proc.stdout)


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
        "required_publication_decision_type": "AUTHORIZE_PUBLICATION",
        "required_override_decision_type": "AUTHORIZE_ONE_SHOT_AGENT_PUBLICATION_OVERRIDE",
        "observations_alone_grant_authority": False,
        "grant_effective_only_when_present_on_main": True,
        "grant_scope_must_equal_unobserved_approved_targets": True,
        "standing_permission": False,
        "auto_publish": "NO_GO",
    }
    if policy != expected_policy:
        errors.append("execution grant policy must remain exact and fail-closed")

    if schema.get("properties", {}).get("mode", {}).get("const") != "ONE_SHOT":
        errors.append("grant schema must remain ONE_SHOT")
    grants = ledger.get("grants")
    if ledger.get("schema_version") != 1 or not isinstance(grants, list) or len(grants) != 1:
        return errors + ["grant ledger must contain exactly one governed grant"]
    grant = grants[0]

    if grant.get("mode") != "ONE_SHOT" or grant.get("status") != "ACTIVE":
        errors.append("current execution grant must be ACTIVE ONE_SHOT")
    if grant.get("authority_anchor_commit") != policy.get("authority_anchor_commit"):
        errors.append("grant authority anchor mismatch")
    if grant.get("base_agent_may_publish") is not False:
        errors.append("base agent permission must remain false")
    if grant.get("scoped_agent_execution_authorized") is not True:
        errors.append("scoped execution authorization missing")
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
    try:
        granted_at = _dt(grant.get("granted_at"))
        expires_at = _dt(grant.get("expires_at"))
        if expires_at <= granted_at:
            errors.append("grant expiry must follow grant time")
        if datetime.now(timezone.utc) >= expires_at.astimezone(timezone.utc):
            errors.append("ACTIVE execution grant is expired")
    except ValueError:
        errors.append("grant timestamps must be timezone-aware")

    items = {i.get("id"): i for i in registry.get("items", []) if isinstance(i, dict)}
    approved = {k: v for k, v in items.items() if v.get("publication_state") == "APPROVED"}
    all_targets = {(item_id, ch) for item_id, item in approved.items() for ch in item.get("target_channels", [])}
    observed_pairs = {(o.get("item_id"), o.get("channel")) for o in observations.get("observations", []) if isinstance(o, dict)}
    missing = all_targets - observed_pairs
    grant_pairs = {(item_id, ch) for item_id in grant.get("item_allowlist", []) for ch in grant.get("channel_allowlist", [])}
    if grant_pairs != missing:
        errors.append("grant scope must equal exact unobserved approved targets")
    if grant.get("original_logical_target_limit") != len(all_targets):
        errors.append("original logical target limit mismatch")
    if grant.get("observed_logical_targets_before_grant") != len(observed_pairs):
        errors.append("observed logical target count mismatch")
    if grant.get("remaining_logical_target_limit") != len(missing):
        errors.append("remaining logical target limit mismatch")
    if grant.get("scope_sha256") != _scope_sha(grant):
        errors.append("grant scope_sha256 mismatch")

    linkedin = distribution.get("channels", {}).get("linkedin", {})
    expected_identity = f"company:{linkedin.get('company_id')}:{linkedin.get('public_slug')}"
    if grant.get("account_identity") != expected_identity:
        errors.append("grant account identity mismatch")
    if set(grant.get("channel_allowlist", [])) != {"LinkedIn"}:
        errors.append("current residual grant may authorize LinkedIn only")

    decision_map = {o.get("observation_id"): o for o in decisions.get("observations", []) if isinstance(o, dict)}
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
        anchored = _anchor_decisions(root, policy["authority_anchor_commit"])
        if anchored is not None:
            anchor_map = {o.get("observation_id"): o for o in anchored.get("observations", []) if isinstance(o, dict)}
            for obs_id in (grant.get("publication_decision_observation_id"), grant.get("override_decision_observation_id")):
                if anchor_map.get(obs_id) != decision_map.get(obs_id):
                    errors.append(f"decision observation not identical to authority anchor: {obs_id}")
    except (ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))

    return errors


def main() -> int:
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
