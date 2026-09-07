import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "openai-publication" / "agent-reliability"
SOURCE_COMMIT = "3a7bff2a139cb6840ab6e23a2c19e315000e8b13"
PLUGIN = "plugins/rumbo-coding-agent-reliability"
SKILLS = [
    "canonical-state-recovery",
    "deep-research-reconcile",
    "goal-loop-controller",
    "execute-verify-close",
    "audit-final-state",
]


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{path}"], cwd=ROOT)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def candidate_skill_digest(skill: str) -> str:
    path = f"openai-publication/agent-reliability/plugin/skills/{skill}/SKILL.md"
    data = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)
    return sha256(data)


def build_source_receipt() -> dict:
    tree = subprocess.check_output(["git", "rev-parse", f"{SOURCE_COMMIT}:{PLUGIN}"], cwd=ROOT, text=True).strip()
    manifest = git_bytes(f"{PLUGIN}/.codex-plugin/plugin.json")
    return {
        "schema": "rumbo.openai-agent-reliability-source/v1",
        "source_repository": "https://github.com/fscfede-beep/Rumbo",
        "source_commit": SOURCE_COMMIT,
        "tree_sha": tree,
        "manifest_sha256": sha256(manifest),
        "skills": SKILLS,
        "skill_sha256": {s: sha256(git_bytes(f"{PLUGIN}/skills/{s}/SKILL.md")) for s in SKILLS},
    }

def write_source_receipt() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    path = PUB / "source-receipt.json"
    path.write_text(json.dumps(build_source_receipt(), indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


if __name__ == "__main__":
    print(write_source_receipt())