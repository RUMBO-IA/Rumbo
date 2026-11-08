"""Read-only PUBLIC Vercel auto-deployment / required-check policy preflight.

This evaluates only the exact simple/minimatch patterns in the observed PUBLIC
vercel.json (literal branches or one terminal *). Unknown glob syntax remains
NOT_PROVEN; no claim is made about manual or owner-authorized deployments.

No network, credentials, environment mutation, deployment or GitHub write.
"""
from __future__ import annotations


def _matches_supported_pattern(pattern: str, branch: str) -> bool | None:
    if not isinstance(pattern, str) or not pattern:
        return None
    # Treat complex minimatch constructs as unknown rather than applying a
    # potentially broader Python fnmatch interpretation to a safety decision.
    if any(char in pattern for char in "?![]{}"):
        return None
    if "*" not in pattern:
        return pattern == branch
    if pattern.count("*") != 1 or not pattern.endswith("*"):
        return None
    prefix = pattern[:-1]
    # minimatch '*' matches within a path segment, not across a slash.
    return branch.startswith(prefix) and "/" not in branch[len(prefix):]


def deployment_enabled(config: dict, branch: str) -> bool | None:
    """Whether Git pushes automatically deploy this branch per Vercel config.

    None means the static expression is not fully understood/validated.
    True only means this configuration does not suppress automatic deployment.
    It does NOT prove a Vercel deployment, status, or GitHub App provenance.
    """
    if not isinstance(config, dict) or not isinstance(branch, str) or not branch:
        return None
    git = config.get("git", {})
    if not isinstance(git, dict):
        return None
    deploy = git.get("deploymentEnabled", True)
    if type(deploy) is bool:
        return deploy
    if not isinstance(deploy, dict):
        return None
    matching: list[bool] = []
    for pattern, value in deploy.items():
        if type(value) is not bool:
            return None
        match = _matches_supported_pattern(pattern, branch)
        if match is None:
            return None
        if match:
            matching.append(value)
    if not matching:
        return True  # documented Vercel default for unmatched branches
    return any(matching)  # a matching true overrides matching false


def required_vercel_check_feasibility(
        config: dict, branch: str, required_checks: tuple[str, ...]) -> dict:
    """Describe a deadlock; never forge a green required check or permit merge."""
    enabled = deployment_enabled(config, branch)
    vercel_required = "Vercel" in required_checks
    conflict = vercel_required and enabled is False
    state = ("BLOCKED_POLICY" if conflict else
             "UNRESOLVED" if enabled is None else
             "REQUIRES_LIVE_CHECK_EVIDENCE")
    return {
        "branch": branch,
        "automatic_deployment_enabled": enabled,
        "required_vercel": vercel_required,
        "policy_conflict": conflict,
        "classification": state,
        "merge_authorized": False,
        "manual_deployment_authority": "NOT_PROVEN",
        "next_safe_action": (
            "Owner-approved source-attributed preview/CI path required; "
            "do not silently change deploymentEnabled or branch protection."
            if conflict else
            "Confirm exact-HEAD Vercel source App check and independent review."
        ),
    }
