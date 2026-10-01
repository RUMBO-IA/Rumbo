#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_SCHEMA = "rumbo.control-plane-authority/v1"
EXPECTED_AUTHORITY_REPO = "RUMBO-IA/Rumbo"
EXPECTED_SOURCE_REPO = "RUMBO-IA/rumbo-control-queue"
EXPECTED_RULE = "ONLY_THIS_PROTECTED_PUBLIC_ANCHOR_SELECTS_CANONICAL_PRIVATE_COMMITS"

class AnchorError(ValueError):
    pass

def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 2

def load_anchor(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnchorError(f"anchor_read: {type(exc).__name__}") from exc
    if not isinstance(data, dict):
        raise AnchorError("anchor_root must be object")
    return data

def validate_static(data: dict) -> None:
    checks = {
        "schema": data.get("schema") == EXPECTED_SCHEMA,
        "authority_repository": data.get("authority_repository") == EXPECTED_AUTHORITY_REPO,
        "authority_ref": data.get("authority_ref") == "main",
        "authority_ref_must_be_protected": data.get("authority_ref_must_be_protected") is True,
        "authority_ruleset_id": isinstance(data.get("authority_ruleset_id"), int) and data["authority_ruleset_id"] > 0,
        "source_repository": data.get("source_repository") == EXPECTED_SOURCE_REPO,
        "source_branch_is_authority": data.get("source_branch_is_authority") is False,
        "canonical_source_commit": isinstance(data.get("canonical_source_commit"), str) and bool(SHA40.fullmatch(data["canonical_source_commit"])),
        "canonical_source_tree": isinstance(data.get("canonical_source_tree"), str) and bool(SHA40.fullmatch(data["canonical_source_tree"])),
        "authority_rule": data.get("authority_rule") == EXPECTED_RULE,
        "production": data.get("production") == "NO_GO",
        "external_spend_usd": data.get("external_spend_usd") == 0,
    }
    required = data.get("authority_required_checks")
    checks["authority_required_checks"] = (
        isinstance(required, list)
        and required
        and all(isinstance(x, str) and x for x in required)
    )
    semantics = data.get("selection_semantics")
    checks["selection_semantics"] = (
        isinstance(semantics, dict)
        and semantics.get("private_commit_is_immutable") is True
        and semantics.get("private_main_may_drift_without_changing_canon") is True
        and semantics.get("anchor_update_requires_protected_public_promotion") is True
        and semantics.get("missing_or_unreadable_anchor") == "NO_CANONICAL_PROMOTION"
        and semantics.get("unlisted_private_commit") == "NON_CANONICAL"
    )
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise AnchorError("invalid fields: " + ",".join(failed))

def gh_json(endpoint: str) -> dict:
    result = subprocess.run(
        ["gh", "api", endpoint],
        text=True, capture_output=True, check=False, timeout=30,
    )
    if result.returncode != 0:
        raise AnchorError(f"gh_api_failed:{endpoint}")
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AnchorError(f"gh_api_invalid_json:{endpoint}") from exc
    if not isinstance(data, dict):
        raise AnchorError(f"gh_api_non_object:{endpoint}")
    return data

def validate_online(data: dict) -> dict:
    source_owner_repo = data["source_repository"]
    source_sha = data["canonical_source_commit"]
    commit = gh_json(f"repos/{source_owner_repo}/git/commits/{source_sha}")
    observed_tree = (commit.get("tree") or {}).get("sha")
    if observed_tree != data["canonical_source_tree"]:
        raise AnchorError("canonical_source_tree mismatch")

    authority_repo = data["authority_repository"]
    authority_ref = data["authority_ref"]
    branch = gh_json(f"repos/{authority_repo}/branches/{authority_ref}")
    if branch.get("protected") is not True:
        raise AnchorError("authority_ref protected=false")
    contexts = set(((branch.get("protection") or {}).get("required_status_checks") or {}).get("contexts") or [])
    missing_checks = sorted(set(data["authority_required_checks"]) - contexts)
    if missing_checks:
        raise AnchorError("authority_required_checks missing:" + ",".join(missing_checks))

    ruleset_id = data["authority_ruleset_id"]
    ruleset = gh_json(f"repos/{authority_repo}/rulesets/{ruleset_id}")
    rule_types = {item.get("type") for item in ruleset.get("rules") or [] if isinstance(item, dict)}
    if ruleset.get("enforcement") != "active":
        raise AnchorError("authority_ruleset enforcement!=active")
    if ruleset.get("bypass_actors"):
        raise AnchorError("authority_ruleset bypass_actors present")
    if "non_fast_forward" not in rule_types:
        raise AnchorError("authority_ruleset missing non_fast_forward")

    source_branch = gh_json(f"repos/{source_owner_repo}/branches/{data['source_branch']}")
    return {
        "source_commit_exists": True,
        "source_tree_matches": True,
        "authority_ref_protected": True,
        "authority_required_checks_present": True,
        "authority_ruleset_active": True,
        "authority_ruleset_no_bypass": True,
        "source_branch_matches_anchor": ((source_branch.get("commit") or {}).get("sha") == source_sha),
    }

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--anchor", type=Path, required=True)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = load_anchor(args.anchor)
        validate_static(data)
        online = None if args.offline else validate_online(data)
    except AnchorError as exc:
        return fail(str(exc))
    payload = {
        "schema": "rumbo.control-plane-authority-verification/v1",
        "status": "PASS",
        "mode": "offline" if args.offline else "online",
        "canonical_source_commit": data["canonical_source_commit"],
        "canonical_source_tree": data["canonical_source_tree"],
        "online": online,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
