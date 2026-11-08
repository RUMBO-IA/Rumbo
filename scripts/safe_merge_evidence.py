import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import safe_merge_policy as policy
import verify_public_privacy
from public_vercel_gate_audit import required_vercel_check_feasibility

BRANCH_RULESET_ID = 22317339


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class EvidenceError(RuntimeError):
    pass


def resolve_command(args, *, which=shutil.which) -> tuple[str, ...]:
    logical = tuple(args)
    if not logical:
        return logical
    resolved = which(logical[0])
    if not resolved:
        return logical
    if Path(resolved).suffix.lower() in {".cmd", ".bat"}:
        command_shell = which("cmd.exe") or "cmd.exe"
        return (command_shell, "/d", "/s", "/c", resolved, *logical[1:])
    return (resolved, *logical[1:])


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
        self.results: list[CommandResult] = []

    def run(self, args, *, env=None) -> CommandResult:
        logical_args = tuple(args)
        execution_args = resolve_command(logical_args)
        effective_env = os.environ.copy()
        if env:
            effective_env.update(env)
        effective_env["CI"] = "1"
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stdout_file, tempfile.TemporaryFile(mode="w+", encoding="utf-8") as stderr_file:
            completed = subprocess.run(
                list(execution_args),
                cwd=self.root,
                env=effective_env,
                stdin=subprocess.DEVNULL,
                text=True,
                stdout=stdout_file,
                stderr=stderr_file,
                check=False,
                timeout=60,
            )
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read()
            stderr = stderr_file.read()
        result = CommandResult(logical_args, completed.returncode, stdout, stderr)
        self.results.append(result)
        return result


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
            "--json", "number,state,baseRefName,headRefName,headRefOid,headRepository,isCrossRepository,isDraft,author,statusCheckRollup",
        ))
        head_repo = data.get("headRepository") or {}
        return {
            "number": data.get("number"),
            "state": str(data.get("state", "")).upper(),
            "base": data.get("baseRefName"),
            "head_branch": data.get("headRefName"),
            "head": data.get("headRefOid"),
            "repo": head_repo.get("nameWithOwner"),
            "cross": data.get("isCrossRepository"),
            "draft": data.get("isDraft"),
            "author": (data.get("author") or {}).get("login"),
        }

    def independent_review_receipt(self, number: int, head_sha: str, author: str) -> dict[str, Any] | None:
        """Require an exact-HEAD review by an authorized non-author account.

        Never treat an earlier approval, self-review or unprivileged user as
        independent authorization. More than one page fails closed.
        """
        if re.fullmatch(r"[0-9a-f]{40}", head_sha) is None:
            raise EvidenceError("review HEAD is malformed")
        if not isinstance(author, str) or not author:
            raise EvidenceError("PR author is missing")
        owner, repo = self.policy.repository.split("/", 1)
        reviews = self._json((
            "gh", "api", f"repos/{owner}/{repo}/pulls/{number}/reviews?per_page=100"
        ))
        if not isinstance(reviews, list) or len(reviews) >= 100:
            raise EvidenceError("review listing unavailable or not exhaustive")
        latest: dict[str, tuple[datetime, int, dict[str, Any]]] = {}
        for review in reviews:
            if not isinstance(review, dict) or not isinstance(review.get("user"), dict):
                raise EvidenceError("malformed PR review record")
            login = review["user"].get("login")
            if not isinstance(login, str) or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", login):
                raise EvidenceError("reviewer identity malformed")
            if review.get("state") == "PENDING":
                continue  # Unsubmitted drafts have no review decision.
            if type(review.get("id")) is not int or review["id"] <= 0:
                return None
            stamp = review.get("submitted_at")
            if not isinstance(stamp, str):
                return None
            try:
                submitted = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                if submitted.utcoffset() is None:
                    return None
            except ValueError:
                return None
            normalized = login.casefold()
            current = latest.get(normalized)
            key = (submitted, review["id"])
            if current is None or key > current[:2]:
                latest[normalized] = (submitted, review["id"], review)
        if any(item[2].get("state") == "CHANGES_REQUESTED" for item in latest.values()):
            return None
        for login, (_, _, review) in sorted(latest.items()):
            if (review["user"].get("type") != "User"
                    or login == author.casefold() or review.get("state") != "APPROVED"
                    or review.get("commit_id") != head_sha
                    or type(review.get("id")) is not int or review["id"] <= 0
                    or not review.get("submitted_at")):
                continue
            permission = self._json((
                "gh", "api", f"repos/{owner}/{repo}/collaborators/{login}/permission"
            ))
            role = permission.get("permission") if isinstance(permission, dict) else None
            if role not in {"write", "maintain", "admin"}:
                continue
            return {
                "review_id": review["id"], "reviewer": login, "author": author,
                "commit_id": head_sha, "state": "APPROVED",
                "permission": role, "submitted_at": review["submitted_at"],
            }
        return None

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
        """Collect exact-HEAD checks without treating an unverified name as authority.

        Github's status API does not independently expose the source App ID
        for a legacy status, so status-only required contexts are NOT_PROVEN.
        """
        if re.fullmatch(r"[0-9a-f]{40}", sha) is None:
            raise EvidenceError("candidate check SHA is malformed")
        owner, repo = self.policy.repository.split("/", 1)
        check_data = self._json(("gh", "api", f"repos/{owner}/{repo}/commits/{sha}/check-runs?per_page=100"))
        if not isinstance(check_data, dict):
            raise EvidenceError("required check listing is malformed")
        runs = check_data.get("check_runs")
        count = check_data.get("total_count")
        if type(count) is not int or not isinstance(runs, list) or count != len(runs):
            raise EvidenceError("required check listing is incomplete or truncated")
        status_data = self._json(("gh", "api", f"repos/{owner}/{repo}/commits/{sha}/status"))
        if not isinstance(status_data, dict) or not isinstance(status_data.get("statuses"), list):
            raise EvidenceError("commit status listing is malformed")
        required_apps = dict(self.policy.required_check_app_ids)
        states: dict[str, str] = {}
        authenticated: dict[str, str] = {}
        unknown_sources: set[str] = set()
        for item in runs:
            if not isinstance(item, dict):
                raise EvidenceError("malformed check run record")
            name = item.get("name")
            if not isinstance(name, str) or not name:
                continue
            if item.get("head_sha") != sha:
                if name in required_apps:
                    unknown_sources.add(name)
                continue
            state = self._check_state(item.get("status"), item.get("conclusion"))
            if name in required_apps:
                app = item.get("app")
                if not isinstance(app, dict) or app.get("id") != required_apps[name]:
                    unknown_sources.add(name)
                    continue
                authenticated[name] = self._merge_check_state(authenticated.get(name), state)
                continue
            states[name] = self._merge_check_state(states.get(name), state)
        states.update(authenticated)
        for item in status_data["statuses"]:
            if not isinstance(item, dict):
                raise EvidenceError("malformed commit status record")
            name = item.get("context")
            if not isinstance(name, str) or not name:
                continue
            if name in required_apps:
                # A status-only required context has no independently proven
                # source App, even when GitHub reports its state as success.
                states.setdefault(name, "UNPROVEN_SOURCE")
                continue
            raw = str(item.get("state", "")).upper()
            state = "SUCCESS" if raw == "SUCCESS" else (raw or "PENDING")
            states[name] = self._merge_check_state(states.get(name), state)
        for name in unknown_sources:
            states.setdefault(name, "UNPROVEN_SOURCE")
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
        """Legacy API intentionally denied.

        Running a verifier loaded from candidate code while passing it private
        deny-list data would cross the PR trust boundary. Use a protected,
        independently attested GitHub App check instead.
        """
        raise EvidenceError(
            "untrusted candidate privacy verifier execution is prohibited; "
            "independent trusted privacy attestation required"
        )

    def commit_metadata_ok(self, candidate: str) -> bool:
        return not verify_public_privacy.commit_metadata_violations(candidate, set())

    def workflow_blob(self, candidate_sha: str) -> dict[str, Any]:
        owner, repo = self.policy.repository.split("/", 1)
        endpoint = f"repos/{owner}/{repo}/contents/{self.policy.privacy_workflow_path}?ref={candidate_sha}"
        data = self._json(("gh", "api", endpoint))
        git_blob = str(data.get("sha") or "")
        if git_blob != self.policy.privacy_workflow_blob:
            raise EvidenceError("privacy workflow Git blob does not match pinned policy")
        if data.get("encoding") != "base64":
            raise EvidenceError("privacy workflow content encoding is not base64")
        encoded = "".join(str(data.get("content") or "").split())
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise EvidenceError("privacy workflow content is invalid base64") from exc
        digest = hashlib.sha256(raw).hexdigest()
        if digest != self.policy.privacy_workflow_sha256:
            raise EvidenceError("privacy workflow SHA-256 does not match pinned policy")
        return {
            "path": self.policy.privacy_workflow_path,
            "git_blob": git_blob,
            "sha256": digest,
        }

    def _require_independent_privacy_check(self, candidate_sha: str) -> dict[str, Any]:
        """Require a check issued by a separately approved GitHub App.

        A workflow step run from PR-provided code is diagnostic evidence only.
        The default policy intentionally has no authorized app, so it denies.
        This method does not execute PR code or access the deny-list secret.
        """
        app_id = self.policy.independent_privacy_app_id
        name = self.policy.independent_privacy_check_name
        if type(app_id) is not int or app_id <= 0 or not isinstance(name, str) or not name:
            raise EvidenceError("independent trusted privacy attestation is not configured")
        if re.fullmatch(r"[0-9a-f]{40}", candidate_sha) is None:
            raise EvidenceError("independent privacy candidate SHA is invalid")
        owner, repo = self.policy.repository.split("/", 1)
        endpoint = f"repos/{owner}/{repo}/commits/{candidate_sha}/check-runs?per_page=100"
        data = self._json(("gh", "api", endpoint))
        runs = data.get("check_runs") if isinstance(data, dict) else None
        count = data.get("total_count") if isinstance(data, dict) else None
        if type(count) is not int or not isinstance(runs, list) or count != len(runs):
            raise EvidenceError("independent privacy check listing is missing or incomplete")
        matches = [item for item in runs if isinstance(item, dict)
                   and item.get("name") == name
                   and isinstance(item.get("app"), dict)
                   and item["app"].get("id") == app_id]
        if len(matches) != 1:
            raise EvidenceError("independent trusted privacy check is missing or ambiguous")
        check = matches[0]
        if (type(check.get("id")) is not int or check["id"] <= 0
                or check.get("head_sha") != candidate_sha
                or check.get("status") != "completed"
                or check.get("conclusion") != "success"
                or not isinstance(check.get("completed_at"), str)
                or not check["completed_at"]):
            raise EvidenceError("independent trusted privacy check is not successful on exact HEAD")
        return {
            "id": check["id"], "app_id": app_id, "name": name,
            "head_sha": candidate_sha, "completed_at": check["completed_at"],
        }

    def _require_executed_private_step(self, run_id: int, candidate_sha: str) -> None:
        """Reject green public runs with an omitted or unbound private gate."""
        if not isinstance(run_id, int) or run_id <= 0:
            raise EvidenceError("private privacy run id is invalid")
        owner, repo = self.policy.repository.split("/", 1)
        data = self._json(("gh", "api", f"repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100"))
        jobs = data.get("jobs")
        count = data.get("total_count")
        if not isinstance(count, int) or not isinstance(jobs, list) or count != len(jobs):
            raise EvidenceError("private privacy job evidence is incomplete")
        matched = [job for job in jobs if isinstance(job, dict) and job.get("name") == "privacy"]
        if len(matched) != 1:
            raise EvidenceError("private privacy job is absent or ambiguous")
        job = matched[0]
        if (job.get("run_id") != run_id or job.get("head_sha") != candidate_sha
                or job.get("status") != "completed" or job.get("conclusion") != "success"):
            raise EvidenceError("private privacy job is not bound to successful exact HEAD")
        steps = job.get("steps")
        if not isinstance(steps, list):
            raise EvidenceError("private privacy step evidence is missing")
        names = {"Verify public privacy invariants",
                 "Verify public privacy invariants (trusted main only)"}
        private_steps = [step for step in steps if isinstance(step, dict)
                         and step.get("name") in names]
        if (len(private_steps) != 1 or private_steps[0].get("status") != "completed"
                or private_steps[0].get("conclusion") != "success"):
            raise EvidenceError("private privacy step did not execute successfully")

    @staticmethod
    def _run_sort_key(run: dict[str, Any]) -> tuple[datetime, int, int]:
        # ISO-8601 strings with different timezone offsets are not
        # lexicographically ordered by actual instant. Validate then compare
        # timezone-aware datetime values so a newer failed run always wins.
        RealEvidence._validate_run_metadata(run)
        instant = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        return (instant, run["run_attempt"], run["id"])

    @staticmethod
    def _validate_run_metadata(run: dict[str, Any]) -> None:
        """Reject ambiguous GitHub run identity before chronological selection."""
        if type(run.get("id")) is not int or run["id"] <= 0:
            raise EvidenceError("privacy workflow run id is malformed")
        if type(run.get("run_attempt")) is not int or run["run_attempt"] <= 0:
            raise EvidenceError("privacy workflow run attempt is malformed")
        created = run.get("created_at")
        if not isinstance(created, str):
            raise EvidenceError("privacy workflow run created_at is missing")
        try:
            timestamp = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError as exc:
            raise EvidenceError("privacy workflow run created_at is malformed") from exc
        if timestamp.utcoffset() is None:
            raise EvidenceError("privacy workflow run created_at must include a timezone")

    def _privacy_workflow_runs(self, candidate_sha: str, event: str) -> list[dict[str, Any]]:
        """Read a complete exact-HEAD workflow listing; never infer from a partial page.

        A newest failed or pending run must not be concealed by pagination.
        We deliberately fail closed on >100 runs until governed pagination
        is implemented; no stale success can become merge authority.
        """
        if re.fullmatch(r"[0-9a-f]{40}", candidate_sha) is None:
            raise EvidenceError("privacy attestation SHA is malformed")
        owner, repo = self.policy.repository.split("/", 1)
        endpoint = f"repos/{owner}/{repo}/actions/workflows/{self.policy.privacy_workflow_id}/runs"
        data = self._json((
            "gh", "api", "--method", "GET", endpoint,
            "-f", f"head_sha={candidate_sha}",
            "-f", f"event={event}",
            "-f", "per_page=100",
        ))
        if not isinstance(data, dict):
            raise EvidenceError("privacy workflow run listing is malformed")
        count = data.get("total_count")
        runs = data.get("workflow_runs")
        if type(count) is not int or not isinstance(runs, list) or count != len(runs):
            raise EvidenceError("privacy workflow run listing is incomplete or truncated")
        if any(not isinstance(item, dict) for item in runs):
            raise EvidenceError("privacy workflow run listing contains malformed records")
        return runs

    def privacy_attestation(self, pr_number: int, candidate_sha: str, target: str, head_branch: str) -> dict[str, Any]:
        workflow = self.workflow_blob(candidate_sha)
        event = policy.attestation_event(target, self.policy)
        runs = self._privacy_workflow_runs(candidate_sha, event)
        matches: list[dict[str, Any]] = []
        for run in runs:
            if (run.get("workflow_id") != self.policy.privacy_workflow_id
                    or run.get("path") != self.policy.privacy_workflow_path
                    or run.get("event") != event
                    or run.get("head_sha") != candidate_sha
                    or run.get("head_branch") != head_branch):
                continue
            # Do not hide a newer failure because GitHub has omitted its
            # pull_requests array. Select latest exact HEAD/branch first,
            # then insist that the selected run belongs to this exact PR.
            self._validate_run_metadata(run)
            matches.append(run)
        if not matches:
            raise EvidenceError("no exact privacy workflow attestation exists")
        if len({run["id"] for run in matches}) != len(matches):
            raise EvidenceError("privacy workflow run identity is ambiguous")
        latest = max(matches, key=self._run_sort_key)
        if event == "pull_request":
            prs = latest.get("pull_requests")
            if (not isinstance(prs, list)
                    or not any(isinstance(item, dict)
                               and type(item.get("number")) is int
                               and item["number"] == pr_number for item in prs)):
                raise EvidenceError("newest privacy workflow run PR association is ambiguous")
        if latest.get("status") != "completed" or latest.get("conclusion") != "success":
            raise EvidenceError("newest exact privacy workflow attestation is not successful")
        independent = self._require_independent_privacy_check(candidate_sha)
        return {
            "independent_privacy_check": independent,
            "workflow_id": self.policy.privacy_workflow_id,
            "workflow_path": workflow["path"],
            "workflow_git_blob": workflow["git_blob"],
            "workflow_sha256": workflow["sha256"],
            "run_id": latest.get("id"),
            "run_attempt": latest.get("run_attempt"),
            "created_at": latest.get("created_at"),
            "event": event,
            "status": latest.get("status"),
            "conclusion": latest.get("conclusion"),
            "head_sha": candidate_sha,
            "head_branch": latest.get("head_branch"),
            "pr_number": pr_number if event == "pull_request" else None,
        }

    def privacy_attestation_by_run(self, previous: dict[str, Any], candidate_sha: str, target: str, head_branch: str) -> dict[str, Any]:
        workflow = self.workflow_blob(candidate_sha)
        event = policy.attestation_event(target, self.policy)
        run_id = previous.get("run_id")
        if not isinstance(run_id, int) or run_id <= 0:
            raise EvidenceError("pre-write privacy attestation run id is invalid")
        owner, repo = self.policy.repository.split("/", 1)
        run = self._json(("gh", "api", f"repos/{owner}/{repo}/actions/runs/{run_id}"))
        if run.get("id") != run_id:
            raise EvidenceError("privacy attestation run id changed")
        if run.get("workflow_id") != self.policy.privacy_workflow_id or run.get("path") != self.policy.privacy_workflow_path:
            raise EvidenceError("privacy attestation workflow identity changed")
        if run.get("event") != event or run.get("head_sha") != candidate_sha or run.get("head_branch") != head_branch:
            raise EvidenceError("privacy attestation commit binding changed")
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            raise EvidenceError("privacy attestation is no longer successful")
        if previous.get("run_attempt") is not None and run.get("run_attempt") != previous.get("run_attempt"):
            raise EvidenceError("privacy attestation attempt changed")
        if previous.get("created_at") and run.get("created_at") != previous.get("created_at"):
            raise EvidenceError("privacy attestation creation time changed")
        # A previously successful run is insufficient if a newer exact-HEAD,
        # same-branch workflow run has since superseded it (including failure).
        # PR association may disappear from run metadata after merge, so use
        # the previously bound run ID plus commit, branch and workflow identity.
        candidates = [
            item for item in self._privacy_workflow_runs(candidate_sha, event)
            if (item.get("workflow_id") == self.policy.privacy_workflow_id
                and item.get("path") == self.policy.privacy_workflow_path
                and item.get("head_sha") == candidate_sha
                and item.get("head_branch") == head_branch
                and item.get("event") == event)
        ]
        if not candidates:
            raise EvidenceError("post-write latest privacy run is not independently observable")
        for candidate in candidates:
            self._validate_run_metadata(candidate)
        if len({item["id"] for item in candidates}) != len(candidates):
            raise EvidenceError("post-write privacy run identity is ambiguous")
        newest = max(candidates, key=self._run_sort_key)
        if (newest.get("id") != run_id
                or newest.get("run_attempt") != run.get("run_attempt")
                or newest.get("status") != "completed"
                or newest.get("conclusion") != "success"):
            raise EvidenceError("post-write privacy receipt was superseded by a newer or invalid run")
        independent = self._require_independent_privacy_check(candidate_sha)
        previous_independent = previous.get("independent_privacy_check")
        if not isinstance(previous_independent, dict) or previous_independent != independent:
            raise EvidenceError("independent trusted privacy receipt changed after write")
        return {
            "independent_privacy_check": independent,
            "workflow_id": self.policy.privacy_workflow_id,
            "workflow_path": workflow["path"],
            "workflow_git_blob": workflow["git_blob"],
            "workflow_sha256": workflow["sha256"],
            "run_id": run_id,
            "run_attempt": run.get("run_attempt"),
            "created_at": run.get("created_at"),
            "event": event,
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "head_sha": candidate_sha,
            "head_branch": run.get("head_branch"),
            "pr_number": previous.get("pr_number"),
        }

    def vercel_required_check_diagnostics(
            self, candidate_sha: str, head_branch: str, required: tuple[str, ...]
    ) -> dict[str, Any]:
        """Read exact candidate config to explain missing required Vercel CI.

        This is NOT a status check or authorization and never invokes Vercel.
        It cannot change branch rules, start deployments, or promote a PR.
        """
        if re.fullmatch(r"[0-9a-f]{40}", candidate_sha) is None:
            raise EvidenceError("diagnostic candidate HEAD is invalid")
        if not isinstance(head_branch, str) or not head_branch:
            raise EvidenceError("diagnostic branch is missing")
        raw = self._run_ok(("git", "show", f"{candidate_sha}:vercel.json")).stdout
        try:
            config = json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise EvidenceError("diagnostic vercel config is invalid") from exc
        if not isinstance(config, dict):
            raise EvidenceError("diagnostic vercel config is not an object")
        return required_vercel_check_feasibility(config, head_branch, tuple(required))

    def vercel_git_deployments_blocked(self, candidate_sha: str, target: str) -> bool:
        result = self._run_ok(("git", "show", f"{candidate_sha}:vercel.json"))
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise EvidenceError("candidate vercel.json is invalid JSON") from exc
        deployment_enabled = (data.get("git") or {}).get("deploymentEnabled")
        if deployment_enabled is False:
            return True
        if not isinstance(deployment_enabled, dict):
            return False
        if deployment_enabled.get(target) is not False:
            return False
        return all(value is False for value in deployment_enabled.values())

    def vercel_state(self) -> dict[str, Any]:
        project = self._json((
            "vercel", "api", f"/v9/projects/{self.policy.vercel_project}",
            "--scope", self.policy.vercel_scope, "--raw",
        ))
        live = self._json((
            "vercel", "api", f"/v13/deployments/{self.policy.live_domain}",
            "--scope", self.policy.vercel_scope, "--raw",
        ))
        return {
            "autoAssignCustomDomains": project.get("autoAssignCustomDomains"),
            "commandForIgnoringBuildStep": project.get("commandForIgnoringBuildStep"),
            "productionBranch": (project.get("link") or {}).get("productionBranch"),
            "gitDeployments": (project.get("gitProviderOptions") or {}).get("createDeployments"),
            "liveDeployment": live.get("id"),
            "liveTarget": live.get("target"),
        }


    def command_log(self) -> list[dict[str, Any]]:
        results = getattr(self.runner, "results", [])
        return [
            {
                "tool": item.args[0] if item.args else "",
                "operation": item.args[1] if len(item.args) > 1 else "",
                "returncode": item.returncode,
            }
            for item in results
        ]

    def ruleset_ok(self) -> bool:
        """Verify the protected ruleset's *meaningful parameters*, not just names.

        A wildcard, negated, duplicated or excluded-branch email rule must not
        qualify as an effective provenance control. Only public regex digests
        from the owner-approved baseline are pinned; secrets are not read.
        """
        owner, repo = self.policy.repository.split("/", 1)
        data = self._json(("gh", "api", f"repos/{owner}/{repo}/rulesets/{BRANCH_RULESET_ID}"))
        if not isinstance(data, dict):
            return False
        ref = (data.get("conditions") or {}).get("ref_name") or {}
        if (data.get("enforcement") != "active"
                or set(ref.get("include") or []) != {"~ALL"}
                or ref.get("exclude") != []
                or data.get("bypass_actors") != []):
            return False
        rules = data.get("rules")
        if not isinstance(rules, list):
            return False
        protected = dict(self.policy.ruleset_pattern_sha256)
        required = set(protected) | {"non_fast_forward"}
        found: dict[str, dict[str, Any]] = {}
        for rule in rules:
            if not isinstance(rule, dict):
                return False
            name = rule.get("type")
            if name not in required:
                continue
            if name in found:
                return False
            found[name] = rule
        if set(found) != required:
            return False
        for name, digest in protected.items():
            params = found[name].get("parameters")
            if not isinstance(params, dict):
                return False
            pattern = params.get("pattern")
            if (params.get("operator") != "regex"
                    or params.get("negate") is not False
                    or not isinstance(pattern, str) or not pattern
                    or hashlib.sha256(pattern.encode("utf-8")).hexdigest() != digest):
                return False
        return True


    def branch_protection_ok(self, target: str, required: tuple[str, ...]) -> bool:
        if target not in self.policy.phase3_targets:
            return True
        owner, repo = self.policy.repository.split("/", 1)
        data = self._json(("gh", "api", f"repos/{owner}/{repo}/branches/{target}/protection"))
        status = data.get("required_status_checks") or {}
        contexts = set(status.get("contexts") or [])
        checks = status.get("checks")
        if not isinstance(checks, list):
            return False
        source_ids: dict[str, int] = {}
        for item in checks:
            if not isinstance(item, dict) or not isinstance(item.get("context"), str):
                return False
            name = item["context"]
            if name in source_ids:
                return False
            source_ids[name] = item.get("app_id")
        contexts.update(source_ids)
        expected_sources = dict(self.policy.required_check_app_ids)
        sources_ok = all(source_ids.get(name) == expected_sources.get(name)
                         and type(source_ids.get(name)) is int
                         for name in required)
        return (
            set(required) <= contexts
            and status.get("strict") is True
            and sources_ok
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
        ancestor = self.runner.run(("git", "merge-base", "--is-ancestor", expected_old, candidate))
        if ancestor.returncode != 0:
            raise EvidenceError("candidate is not a fast-forward descendant of expected target")
        # The ancestry guard prevents history rewrites; the exact lease prevents
        # advancing a target that changed between verification and the push.
        result = self.runner.run((
            "git", "push", f"--force-with-lease=refs/heads/{target}:{expected_old}",
            "origin", f"{candidate}:refs/heads/{target}",
        ))
        if result.returncode != 0:
            raise EvidenceError("fast-forward push failed")
        return result
