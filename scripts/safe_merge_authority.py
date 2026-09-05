from dataclasses import dataclass
from typing import Any

import safe_merge_policy as policy


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    evidence: dict[str, Any]


@dataclass(frozen=True)
class MergeOutcome:
    state: str
    failed_gate: str | None
    gates: tuple[GateResult, ...]
    pre_write_target_sha: str | None = None
    live_deployment_before: str | None = None


def _stop(gates, gate: str, evidence: dict[str, Any], *, target_sha=None, live=None) -> MergeOutcome:
    gates.append(GateResult(gate, False, evidence))
    return MergeOutcome("SAFE_STOP", gate, tuple(gates), target_sha, live)


def _post_fail(gates, evidence: dict[str, Any], *, target_sha=None, live=None) -> MergeOutcome:
    gates.append(GateResult("POST_WRITE_VERIFY", False, evidence))
    return MergeOutcome("POST_WRITE_VERIFY_FAILED", "POST_WRITE_VERIFY", tuple(gates), target_sha, live)


def _required_checks(target: str, merge_policy: policy.MergePolicy) -> tuple[str, ...]:
    if target in merge_policy.required_checks:
        return merge_policy.required_checks[target]
    if target.startswith(merge_policy.probe_prefix):
        return merge_policy.required_checks["main"]
    raise policy.PolicyError("required checks are undefined for target")


def evaluate(request: policy.MergeRequest, merge_policy: policy.MergePolicy, evidence, mode: str = "dry-run") -> MergeOutcome:
    gates: list[GateResult] = []
    current_gate = "POLICY"
    target_sha: str | None = None
    live_id: str | None = None
    try:
        policy.validate_request(request, merge_policy)
        policy.validate_execution_mode(mode, request.expected_base, merge_policy)

        current_gate = "PR_IDENTITY"
        pr = evidence.pr(request.pr_number)
        identity_ok = (
            pr.get("state") == "OPEN"
            and pr.get("base") == request.expected_base
            and pr.get("head") == request.expected_head_sha
            and pr.get("repo") == request.repository
            and not pr.get("cross")
        )
        if not identity_ok:
            return _stop(gates, current_gate, {"reason": "PR identity drift"})
        gates.append(GateResult(current_gate, True, {"head": request.expected_head_sha, "base": request.expected_base}))

        current_gate = "REQUIRED_CHECKS"
        states = evidence.checks(request.expected_head_sha)
        required = _required_checks(request.expected_base, merge_policy)
        missing_or_bad = {name: states.get(name, "MISSING") for name in required if states.get(name) != "SUCCESS"}
        if missing_or_bad:
            return _stop(gates, current_gate, {"checks": missing_or_bad})
        gates.append(GateResult(current_gate, True, {"checks": {name: "SUCCESS" for name in required}}))

        current_gate = "PRIVACY_ANCESTRY"
        target_sha = evidence.target_sha(request.expected_base)
        if not evidence.is_ancestor(target_sha, request.expected_head_sha):
            return _stop(gates, current_gate, {"reason": "candidate is not descendant"}, target_sha=target_sha)
        if not evidence.privacy_ok(request.expected_head_sha):
            return _stop(gates, current_gate, {"reason": "privacy verification failed"}, target_sha=target_sha)
        gates.append(GateResult(current_gate, True, {"target_sha": target_sha, "candidate": request.expected_head_sha}))

        current_gate = "PRODUCTION_NO_GO"
        vercel = evidence.vercel_state()
        live_id = vercel.get("liveDeployment")
        production_ok = (
            vercel.get("autoAssignCustomDomains") is False
            and vercel.get("commandForIgnoringBuildStep") in (None, "")
            and vercel.get("productionBranch") == "main"
            and bool(live_id)
            and vercel.get("liveTarget") == "production"
        )
        if not production_ok:
            return _stop(gates, current_gate, {"reason": "Vercel production safety drift"}, target_sha=target_sha, live=live_id)
        gates.append(GateResult(current_gate, True, {"liveDeployment": live_id}))

        current_gate = "FAST_FORWARD_ONLY"
        if not evidence.ruleset_ok():
            return _stop(gates, current_gate, {"reason": "branch ruleset drift"}, target_sha=target_sha, live=live_id)
        fresh_target = evidence.target_sha(request.expected_base)
        if fresh_target != target_sha:
            return _stop(gates, current_gate, {"reason": "target changed before write", "fresh_target": fresh_target}, target_sha=target_sha, live=live_id)
        gates.append(GateResult(current_gate, True, {"target_sha": target_sha, "ruleset": "active"}))

        if mode == "dry-run":
            return MergeOutcome("DRY_RUN_PASS", None, tuple(gates), target_sha, live_id)

        evidence.fast_forward(request.expected_base, target_sha, request.expected_head_sha)

        post_target = evidence.target_sha(request.expected_base)
        if post_target != request.expected_head_sha:
            return _post_fail(gates, {"reason": "target SHA mismatch", "observed": post_target}, target_sha=target_sha, live=live_id)

        post_checks = evidence.checks(request.expected_head_sha)
        if any(post_checks.get(name) != "SUCCESS" for name in required):
            return _post_fail(gates, {"reason": "required checks changed after write"}, target_sha=target_sha, live=live_id)
        if not evidence.privacy_ok(request.expected_head_sha):
            return _post_fail(gates, {"reason": "privacy verification failed after write"}, target_sha=target_sha, live=live_id)
        if not evidence.ruleset_ok():
            return _post_fail(gates, {"reason": "ruleset drift after write"}, target_sha=target_sha, live=live_id)
        if not evidence.branch_protection_ok(request.expected_base, required):
            return _post_fail(gates, {"reason": "branch protection drift after write"}, target_sha=target_sha, live=live_id)

        post_vercel = evidence.vercel_state()
        post_prod_ok = (
            post_vercel.get("autoAssignCustomDomains") is False
            and post_vercel.get("commandForIgnoringBuildStep") in (None, "")
            and post_vercel.get("productionBranch") == "main"
            and post_vercel.get("liveDeployment") == live_id
            and post_vercel.get("liveTarget") == "production"
        )
        if not post_prod_ok:
            return _post_fail(gates, {"reason": "Vercel drift after write"}, target_sha=target_sha, live=live_id)

        gates.append(GateResult("POST_WRITE_VERIFY", True, {"target": post_target, "liveDeployment": live_id}))
        return MergeOutcome("MERGED_SAFE", None, tuple(gates), target_sha, live_id)
    except Exception as exc:
        return _stop(
            gates,
            current_gate,
            {"reason": "exception", "type": type(exc).__name__},
            target_sha=target_sha,
            live=live_id,
        )
