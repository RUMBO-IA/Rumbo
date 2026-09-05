import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import safe_merge_policy as policy
import verify_public_privacy

BRANCH_RULESET_ID = 22317339


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class EvidenceError(RuntimeError):
    pass


def parse_json_result(result: CommandResult) -> Any:
    if result.returncode != 0:
        raise EvidenceError(f"command failed ({result.returncode}): {' '.join(result.args)}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise EvidenceError("command returned invalid JSON") from exc


class SubprocessRunner:
    def __init__(self, root: Path):
        self.root = root

    def run(self, args, *, env=None) -> CommandResult:
        completed = subprocess.run(
            list(args),
            cwd=self.root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        return CommandResult(tuple(args), completed.returncode, completed.stdout, completed.stderr)


class RealEvidence:
    def __init__(self, root: Path, runner=None, merge_policy=policy.DEFAULT_POLICY):
        self.root = Path(root)
        self.runner = runner or SubprocessRunner(self.root)
        self.policy = merge_policy

    def _json(self, args) -> Any:
        return parse_json_result(self.runner.run(tuple(args)))
    def pr(self, number: int) -> dict[str, Any]:
        data = self._json((
            "gh", "pr", "view", str(number),
            "-R", self.policy.repository,
            "--json", "number,state,baseRefName,headRefOid,headRepository,isCrossRepository,statusCheckRollup",
        ))
        head_repo = data.get("headRepository") or {}
        return {
            "number": data.get("number"),
            "state": str(data.get("state", "")).upper(),
            "base": data.get("baseRefName"),
            "head": data.get("headRefOid"),
            "repo": head_repo.get("nameWithOwner"),
            "cross": bool(data.get("isCrossRepository")),
        }

    @staticmethod
    def _check_state(status: str | None, conclusion: str | None) -> str:
        if status and status.lower() != "completed":
            return "PENDING"
        if conclusion is None:
            return "PENDING"
        return conclusion.upper()

    @staticmethod
    def _merge_check_state(old: str | None, new: str) -> str:
        if old is None or old == "SUCCESS":
            return new
        return old
    def checks(self, sha: str) -> dict[str, str]:
        owner, repo = self.policy.repository.split("/", 1)
        check_data = self._json(("gh", "api", f"repos/{owner}/{repo}/commits/{sha}/check-runs"))
        status_data = self._json(("gh", "api", f"repos/{owner}/{repo}/commits/{sha}/status"))
        states: dict[str, str] = {}
        for item in check_data.get("check_runs", []):
            name = item.get("name")
            if not name:
                continue
            state = self._check_state(item.get("status"), item.get("conclusion"))
            states[name] = self._merge_check_state(states.get(name), state)
        for item in status_data.get("statuses", []):
            name = item.get("context")
            if not name:
                continue
            raw = str(item.get("state", "")).upper()
            state = "SUCCESS" if raw == "SUCCESS" else (raw or "PENDING")
            states[name] = self._merge_check_state(states.get(name), state)
        return states

    def _run_ok(self, args, *, allowed=(0,)) -> CommandResult:
        result = self.runner.run(tuple(args))
        if result.returncode not in allowed:
            raise EvidenceError(f"command failed ({result.returncode}): {' '.join(result.args)}")
        return result
    def fetch_public_refs(self) -> None:
        self._run_ok((
            "git", "fetch", "--prune", "origin",
            "+refs/heads/*:refs/remotes/origin/*",
            "+refs/tags/*:refs/tags/*",
        ))

    def target_sha(self, target: str) -> str:
        self.fetch_public_refs()
        result = self._run_ok(("git", "rev-parse", f"refs/remotes/origin/{target}"))
        return result.stdout.strip()

    def is_ancestor(self, base_sha: str, candidate: str) -> bool:
        result = self.runner.run(("git", "merge-base", "--is-ancestor", base_sha, candidate))
        if result.returncode == 0:
            return True
        if result.returncode == 1:
            return False
        raise EvidenceError("git merge-base failed")

    @staticmethod
    def _deny_hashes() -> set[str]:
        raw = os.environ.get("RUMBO_PRIVACY_DENY_HASHES", "")
        values = {item.strip().lower() for item in raw.split(",") if item.strip()}
        if not values or any(re.fullmatch(r"[0-9a-f]{64}", item) is None for item in values):
            raise EvidenceError("privacy deny-hash evidence is missing or malformed")
        return values
    def privacy_ok(self, candidate: str) -> bool:
        deny = self._deny_hashes()
        if verify_public_privacy.commit_metadata_violations(candidate, deny):
            return False
        with tempfile.TemporaryDirectory(prefix="rumbo-safe-privacy-") as td:
            candidate_root = Path(td) / "candidate"
            added = self.runner.run(("git", "worktree", "add", "--detach", str(candidate_root), candidate))
            if added.returncode != 0:
                raise EvidenceError("could not create candidate privacy worktree")
            try:
                env = os.environ.copy()
                env["RUMBO_PRIVACY_COMMIT_SHA"] = candidate
                env["RUMBO_PRIVACY_SCAN_ALL_REFS"] = "1"
                check = self.runner.run(
                    (sys.executable, str(candidate_root / "scripts" / "verify_public_privacy.py")),
                    env=env,
                )
                return check.returncode == 0 and "PRIVACY_GATE_PASS" in check.stdout
            finally:
                cleanup = self.runner.run(("git", "worktree", "remove", "--force", str(candidate_root)))
                if cleanup.returncode != 0:
                    raise EvidenceError("candidate privacy worktree cleanup failed")

    def vercel_state(self) -> dict[str, Any]:
        project = self._json((
            "vercel", "api", f"/v9/projects/{self.policy.vercel_project}",
            "--scope", self.policy.vercel_scope, "--raw",
        ))
        live = self._json((
            "vercel", "inspect", self.policy.live_domain,
            "--scope", self.policy.vercel_scope, "--json",
        ))
        return {
            "autoAssignCustomDomains": project.get("autoAssignCustomDomains"),
            "commandForIgnoringBuildStep": project.get("commandForIgnoringBuildStep"),
            "productionBranch": (project.get("link") or {}).get("productionBranch"),
            "liveDeployment": live.get("id"),
            "liveTarget": live.get("target"),
        }

    def ruleset_ok(self) -> bool:
        owner, repo = self.policy.repository.split("/", 1)
        data = self._json(("gh", "api", f"repos/{owner}/{repo}/rulesets/{BRANCH_RULESET_ID}"))
        rule_types = {item.get("type") for item in data.get("rules", [])}
        includes = set((data.get("conditions") or {}).get("ref_name", {}).get("include", []))
        return (
            data.get("enforcement") == "active"
            and "~ALL" in includes
            and not data.get("bypass_actors")
            and {"commit_author_email_pattern", "committer_email_pattern", "non_fast_forward"} <= rule_types
        )


    def branch_protection_ok(self, target: str, required: tuple[str, ...]) -> bool:
        if target not in self.policy.phase3_targets:
            return True
        owner, repo = self.policy.repository.split("/", 1)
        data = self._json(("gh", "api", f"repos/{owner}/{repo}/branches/{target}/protection"))
        status = data.get("required_status_checks") or {}
        contexts = set(status.get("contexts") or [])
        contexts.update(item.get("context") for item in status.get("checks") or [] if item.get("context"))
        return (
            set(required) <= contexts
            and bool((data.get("enforce_admins") or {}).get("enabled"))
            and bool((data.get("required_linear_history") or {}).get("enabled"))
            and not bool((data.get("allow_force_pushes") or {}).get("enabled"))
            and bool((data.get("required_conversation_resolution") or {}).get("enabled"))
        )

    def fast_forward(self, target: str, expected_old: str, candidate: str) -> CommandResult:
        authorized = target in self.policy.phase3_targets or target.startswith(self.policy.probe_prefix)
        if not authorized:
            raise EvidenceError("target is outside safe-merge policy")
        check_ref = self.runner.run(("git", "check-ref-format", f"refs/heads/{target}"))
        if check_ref.returncode != 0:
            raise EvidenceError("target is not a valid branch ref")
        if self.target_sha(target) != expected_old:
            raise EvidenceError("target changed at write boundary")
        result = self.runner.run(("git", "push", "origin", f"{candidate}:refs/heads/{target}"))
        if result.returncode != 0:
            raise EvidenceError("fast-forward push failed")
        return result
