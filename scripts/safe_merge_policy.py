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
