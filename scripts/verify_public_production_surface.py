from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "docs" / "brand" / "production_lock_v1.json"
SOURCE_PATH = "index.html"


def normalize_html(raw: bytes) -> bytes:
    text = raw.decode("utf-8")
    return text.replace("\r\n", "\n").encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_lock(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    for key in ("application_sha", "deployment_id", "domain", "status"):
        if not data.get(key):
            raise ValueError(f"production lock missing {key}")
    if data["status"] != "AUTHORIZED":
        raise ValueError("production lock is not AUTHORIZED")
    return data


def read_authorized_source(root: pathlib.Path, app_sha: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{app_sha}:{SOURCE_PATH}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"authorized source read failed: {detail}")
    return proc.stdout


def fetch_live(domain: str, timeout: float = 15.0) -> bytes:
    req = urllib.request.Request(
        f"https://{domain}/",
        headers={"User-Agent": "RUMBO-Production-Surface-Watch/1"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"live HTTP status is {response.status}, expected 200")
        return response.read()


def compare_surface(source_raw: bytes, live_raw: bytes) -> dict:
    source = normalize_html(source_raw)
    live = normalize_html(live_raw)
    return {
        "source_bytes": len(source),
        "live_bytes": len(live),
        "source_sha256": sha256(source),
        "live_sha256": sha256(live),
        "match": source == live,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=pathlib.Path, default=DEFAULT_LOCK)
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args(argv)

    try:
        lock = load_lock(args.lock)
        source_raw = read_authorized_source(args.repo_root, lock["application_sha"])
        live_raw = fetch_live(lock["domain"], timeout=args.timeout)
        comparison = compare_surface(source_raw, live_raw)
        result = {
            "schema": "rumbo.brand.public-production-surface-verification/v1",
            "domain": lock["domain"],
            "application_sha": lock["application_sha"],
            "deployment_id": lock["deployment_id"],
            **comparison,
            "status": "PASS" if comparison["match"] else "DRIFT",
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if comparison["match"] else 1
    except Exception as exc:
        print(json.dumps({
            "schema": "rumbo.brand.public-production-surface-verification/v1",
            "status": "NOT_VERIFIED",
            "error": str(exc),
        }, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
