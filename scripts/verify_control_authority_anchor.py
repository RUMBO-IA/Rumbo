#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SHA40 = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_SCHEMA = "rumbo.public-protected-authority-anchor/v1"
EXPECTED_AUTHORITY_REPO = "RUMBO-IA/Rumbo"
EXPECTED_SOURCE_REPO = "RUMBO-IA/rumbo-control-queue"
EXPECTED_EFFECT = "PRIVATE_CONTROL_PROMOTION_ANCHOR"


class AnchorError(ValueError):
    pass


def load_anchor(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AnchorError(f"anchor_read:{type(exc).__name__}") from exc
    if not isinstance(data, dict):
        raise AnchorError("anchor_root must be object")
    return data


def validate_static(data: dict) -> None:
    public = data.get("public_authority")
    subject = data.get("subject")
    native = data.get("private_native_enforcement")
    policy = data.get("policy")
    semantics = data.get("selection_semantics")

    checks = {
        "schema": data.get("schema") == EXPECTED_SCHEMA,
        "authority_effect": data.get("authority_effect") == EXPECTED_EFFECT,
        "public_authority": isinstance(public, dict),
        "subject": isinstance(subject, dict),
        "private_native_enforcement": isinstance(native, dict),
        "policy": isinstance(policy, dict),
        "selection_semantics": isinstance(semantics, dict),
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise AnchorError("invalid fields:" + ",".join(failed))

    required = ((public.get("required_readback") or {}).get("required_status_checks"))
    static = {
        "public repository": public.get("repository") == EXPECTED_AUTHORITY_REPO,
        "public branch": public.get("branch") == "main",
        "public protected requirement": (public.get("required_readback") or {}).get("protected") is True,
        "authority_ruleset_id": isinstance(public.get("ruleset_id"), int) and public["ruleset_id"] > 0,
        "required_status_checks": (
            isinstance(required, list)
            and set(required) == {"privacy", "Vercel"}
        ),
        "subject kind": subject.get("kind") == "PRIVATE_CONTROL_REPOSITORY",
        "subject repository": subject.get("repository") == EXPECTED_SOURCE_REPO,
        "repository_identity_sha256": (
            isinstance(subject.get("repository_identity_sha256"), str)
            and bool(re.fullmatch(r"[0-9a-f]{64}", subject["repository_identity_sha256"]))
        ),
        "authorized_main_sha": (
            isinstance(subject.get("authorized_main_sha"), str)
            and bool(SHA40.fullmatch(subject["authorized_main_sha"]))
        ),
        "authorized_tree_sha": (
            isinstance(subject.get("authorized_tree_sha"), str)
            and bool(SHA40.fullmatch(subject["authorized_tree_sha"]))
        ),
        "private must remain private": native.get("private_repository_must_remain_private") is True,
        "exact sha required": policy.get("canonical_private_state_requires_exact_sha_match") is True,
        "private main non-authoritative": policy.get("private_main_alone_is_not_promotion_authority") is True,
        "public promotion required": policy.get("public_anchor_update_requires_protected_public_path") is True,
        "production": policy.get("production") == "NO_GO",
        "external_spend": policy.get("external_spend_usd") == 0,
        "no paid upgrade": policy.get("paid_upgrade_authorized") is False,
        "no public private repo": policy.get("make_private_repo_public_authorized") is False,
        "immutable private commit": semantics.get("private_commit_is_immutable") is True,
        "private main drift allowed": semantics.get("private_main_may_drift_without_changing_canon") is True,
        "anchor update protected": semantics.get("anchor_update_requires_protected_public_promotion") is True,
        "missing anchor fails closed": semantics.get("missing_or_unreadable_anchor") == "NO_CANONICAL_PROMOTION",
        "unlisted commit noncanonical": semantics.get("unlisted_private_commit") == "NON_CANONICAL",
    }
    failed = [name for name, ok in static.items() if not ok]
    if failed:
        raise AnchorError("invalid fields:" + ",".join(failed))


def gh_json(endpoint: str) -> dict:
    result = subprocess.run(
        ["gh", "api", endpoint],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
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
    public = data["public_authority"]
    subject = data["subject"]

    source_repo = subject["repository"]
    authorized = subject["authorized_main_sha"]
    commit = gh_json(f"repos/{source_repo}/git/commits/{authorized}")
    observed_tree = (commit.get("tree") or {}).get("sha")
    if observed_tree != subject["authorized_tree_sha"]:
        raise AnchorError("authorized_tree_sha mismatch")

    authority_repo = public["repository"]
    authority_branch = public["branch"]
    branch = gh_json(f"repos/{authority_repo}/branches/{authority_branch}")
    if branch.get("protected") is not True:
        raise AnchorError("public authority protected=false")

    contexts = set(
        (((branch.get("protection") or {}).get("required_status_checks") or {}).get("contexts") or [])
    )
    required = set((public.get("required_readback") or {}).get("required_status_checks") or [])
    missing = sorted(required - contexts)
    if missing:
        raise AnchorError("missing required checks:" + ",".join(missing))

    ruleset_id = public["ruleset_id"]
    ruleset = gh_json(f"repos/{authority_repo}/rulesets/{ruleset_id}")
    if ruleset.get("enforcement") != "active":
        raise AnchorError("ruleset enforcement!=active")
    if ruleset.get("bypass_actors"):
        raise AnchorError("ruleset bypass_actors present")
    rule_types = {
        rule.get("type")
        for rule in (ruleset.get("rules") or [])
        if isinstance(rule, dict)
    }
    if "non_fast_forward" not in rule_types:
        raise AnchorError("ruleset missing non_fast_forward")

    source_branch = gh_json(f"repos/{source_repo}/branches/main")
    current_source_main = (source_branch.get("commit") or {}).get("sha")

    return {
        "canonical_source_commit": authorized,
        "canonical_source_tree": subject["authorized_tree_sha"],
        "source_commit_exists": True,
        "source_tree_matches": True,
        "public_authority_protected": True,
        "required_checks_present": True,
        "ruleset_active": True,
        "ruleset_no_bypass": True,
        "ruleset_non_fast_forward": True,
        "source_branch_protected": source_branch.get("protected") is True,
        "source_branch_current_sha": current_source_main,
        "source_branch_matches_anchor": current_source_main == authorized,
        "private_main_drift_changes_canon": False,
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
        print(str(exc), file=sys.stderr)
        return 2

    payload = {
        "schema": "rumbo.public-protected-authority-anchor-verification/v1",
        "status": "PASS",
        "mode": "offline" if args.offline else "online",
        "canonical_source_commit": data["subject"]["authorized_main_sha"],
        "canonical_source_tree": data["subject"]["authorized_tree_sha"],
        "online": online,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
