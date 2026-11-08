import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MergeRequest:
    pr_number: int
    expected_head_sha: str
    expected_base: str
    repository: str


@dataclass(frozen=True)
class MergePolicy:
    repository: str
    phase3_targets: frozenset[str]
    probe_prefix: str
    required_checks: dict[str, tuple[str, ...]]
    vercel_project: str
    vercel_scope: str
    live_domain: str
    privacy_workflow_id: int
    privacy_workflow_path: str
    privacy_workflow_blob: str
    privacy_workflow_sha256: str
    # Only an owner-approved independent GitHub App may attest private validation.
    # Unset by default: a successful Actions step is not private authorization.
    independent_privacy_app_id: int | None = None
    independent_privacy_check_name: str = "RUMBO Protected Privacy Attestation"
    # Pinned to verified GitHub branch-protection source App IDs, NOT permissions.
    required_check_app_ids: tuple[tuple[str, int], ...] = (
        ("privacy", 15368), ("Vercel", 8329),
    )
    # Immutable fingerprints of the current owner-configured PUBLIC ruleset
    # email allowlists; these are NOT secret material.
    ruleset_pattern_sha256: tuple[tuple[str, str], ...] = (
        ("commit_author_email_pattern", "bbbec65e2c4f00bf44a325e8dd9a7cd27bf7ff9c8b4bc1fd7143a382706ea387"),
        ("committer_email_pattern", "452219b9999b80d075fe962e6f9be1ff47c41be6d1ca7f8a0cbbecfa1910b810"),
    )


class PolicyError(ValueError):
    pass


DEFAULT_POLICY = MergePolicy(
    repository="RUMBO-IA/Rumbo",
    phase3_targets=frozenset({"main"}),
    probe_prefix="probe/safe-merge-",
    required_checks={"main": ("privacy", "Vercel")},
    vercel_project="rumbo-ia-publica",
    vercel_scope="agent-ai-ingenieria",
    live_domain="rumbo.verso.fans",
    privacy_workflow_id=347174988,
    privacy_workflow_path=".github/workflows/privacy-gate.yml",
    privacy_workflow_blob="7ebdcd9c3e8bc13a03f569212c2a9c7a0c0d7124",
    privacy_workflow_sha256="29fc3b7403502a20f873e6627c073c82083fab6d95ed7dca82a56ab9f4923151",
)


def validate_request(request: MergeRequest, merge_policy: MergePolicy) -> None:
    if request.repository != merge_policy.repository:
        raise PolicyError("repository is not authorized")
    if request.pr_number <= 0:
        raise PolicyError("PR number must be positive")
    if re.fullmatch(r"[0-9a-f]{40}", request.expected_head_sha) is None:
        raise PolicyError("expected head SHA must be 40 lowercase hex characters")
    if not request.expected_base or request.expected_base.startswith("refs/"):
        raise PolicyError("base branch must be a plain branch name")


def validate_execution_mode(mode: str, target: str, merge_policy: MergePolicy) -> None:
    phase3 = target in merge_policy.phase3_targets
    probe = target.startswith(merge_policy.probe_prefix)
    if mode == "main" and phase3:
        return
    if mode == "probe" and probe:
        return
    if mode == "dry-run" and (phase3 or probe):
        return
    raise PolicyError(f"mode {mode!r} is not authorized for target {target!r}")


def attestation_event(target: str, merge_policy: MergePolicy) -> str:
    if target in merge_policy.phase3_targets:
        return "pull_request"
    if target.startswith(merge_policy.probe_prefix):
        return "push"
    raise PolicyError("privacy attestation event is undefined for target")
