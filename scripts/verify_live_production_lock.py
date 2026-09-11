from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "docs" / "brand" / "production_lock_v1.json"


def evaluate(lock: dict, inspect_data: dict, metadata: dict) -> list[str]:
    errors: list[str] = []
    expected_deployment = lock.get("deployment_id")
    expected_sha = lock.get("application_sha")
    if inspect_data.get("id") != expected_deployment:
        errors.append(f"alias deployment drift: expected {expected_deployment}, got {inspect_data.get('id')}")
    if metadata.get("id") != expected_deployment:
        errors.append(f"metadata deployment drift: expected {expected_deployment}, got {metadata.get('id')}")
    if inspect_data.get("target") != "production" or metadata.get("target") != "production":
        errors.append("production target mismatch")
    if inspect_data.get("readyState") != "READY" or metadata.get("readyState") != "READY":
        errors.append("production ready state mismatch")
    observed_sha = (metadata.get("meta") or {}).get("githubCommitSha")
    if observed_sha != expected_sha:
        errors.append(f"Git SHA drift: expected {expected_sha}, got {observed_sha}")
    return errors


def _run_json(argv: list[str]) -> dict:
    proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        detail = proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else f"exit {proc.returncode}"
        raise RuntimeError(f"command failed: {detail}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("command did not return valid JSON") from exc


def observe(lock: dict, scope: str, team_id: str, vercel_bin: str | None = None) -> tuple[dict, dict]:
    binary = vercel_bin or shutil.which("vercel.cmd") or shutil.which("vercel")
    if not binary:
        raise RuntimeError("Vercel CLI not found")
    domain = str(lock["domain"])
    inspect_data = _run_json([
        binary, "inspect", domain, "--json", "--scope", scope, "--no-color", "--non-interactive"
    ])
    deployment_id = str(inspect_data.get("id") or "")
    if not deployment_id:
        raise RuntimeError("Vercel inspect returned no deployment id")
    endpoint = f"/v13/deployments/{deployment_id}?teamId={team_id}"
    metadata = _run_json([
        binary, "api", endpoint, "--raw", "--scope", scope, "--no-color", "--non-interactive"
    ])
    return inspect_data, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify live Vercel production against the canonical RUMBO production lock.")
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--scope", required=True)
    parser.add_argument("--team-id", required=True)
    parser.add_argument("--vercel-bin")
    args = parser.parse_args()

    lock_path = pathlib.Path(args.lock)
    lock = json.loads(lock_path.read_text(encoding="utf-8-sig"))
    inspect_data, metadata = observe(lock, args.scope, args.team_id, args.vercel_bin)
    errors = evaluate(lock, inspect_data, metadata)
    result = {
        "schema": "rumbo.brand.live-production-lock-verification/v1",
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "domain": lock.get("domain"),
        "expected": {
            "deployment_id": lock.get("deployment_id"),
            "application_sha": lock.get("application_sha"),
        },
        "observed": {
            "deployment_id": inspect_data.get("id"),
            "application_sha": (metadata.get("meta") or {}).get("githubCommitSha"),
            "target": metadata.get("target"),
            "ready_state": metadata.get("readyState"),
        },
        "errors": errors,
        "status": "PASS" if not errors else "FAIL_CLOSED",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())