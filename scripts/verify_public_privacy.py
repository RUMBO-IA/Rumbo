import hashlib
import json
import os
import re
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NAME = "Sebastián Federico"
PUBLIC_PLUGIN_METADATA = {
    Path(".agents/plugins/marketplace.json"),
    Path("plugins/rumbo-coding-agent-reliability/.codex-plugin/plugin.json"),
}
PERSONAL_EMAIL_RE = re.compile(r"(?i)\b[\w.+-]+@(gmail|hotmail|outlook|yahoo|icloud)\.[a-z]{2,}\b")
PRIVATE_LINKEDIN_RE = re.compile(r"(?i)linkedin\.com/in/")
ZERO_SHA = "0" * 40


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(value.split())


def sha(value: str) -> str:
    return hashlib.sha256(norm(value).encode("utf-8")).hexdigest()


def tracked_files() -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    return [ROOT / p.decode("utf-8") for p in raw.split(b"\0") if p]


def text_of(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def candidates(text: str):
    words = re.findall(r"[^\W_]+(?:[-'][^\W_]+)*", text, flags=re.UNICODE)
    for size in range(1, 5):
        for i in range(0, len(words) - size + 1):
            yield " ".join(words[i : i + size])


def new_commits(head: str, base: str | None) -> list[str]:
    if not base or base == ZERO_SHA:
        return [head]
    raw = subprocess.check_output(
        ["git", "rev-list", "--reverse", f"{base}..{head}"], cwd=ROOT, text=True
    )
    commits = [line.strip() for line in raw.splitlines() if line.strip()]
    return commits or [head]


def validate_commit_metadata(commit: str, violations: list[str]) -> None:
    fmt = "%an%x00%ae%x00%ce"
    raw = subprocess.check_output(
        ["git", "show", "-s", f"--format={fmt}", commit], cwd=ROOT, text=True
    ).rstrip("\n")
    author_name, author_email, committer_email = raw.split("\x00")
    approved_names = {PUBLIC_NAME, "fscfede-beep"}
    approved_emails = {
        "sebastian@rumbo.verso.fans",
        "293577326+fscfede-beep@users.noreply.github.com",
    }
    short = commit[:12]
    if author_name not in approved_names:
        violations.append(f"git:{short}:author-name")
    if author_email not in approved_emails:
        violations.append(f"git:{short}:author-email")
    if committer_email not in approved_emails and committer_email != "noreply@github.com":
        violations.append(f"git:{short}:committer-email")


def validate_public_plugin_metadata(relpath: Path, text: str, violations: list[str]) -> None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        violations.append(f"{relpath.as_posix()}:invalid-json")
        return
    serialized = json.dumps(data, ensure_ascii=False, sort_keys=True)
    if PUBLIC_NAME.casefold() in serialized.casefold():
        violations.append(f"{relpath.as_posix()}:private-full-name")
    if PERSONAL_EMAIL_RE.search(serialized):
        violations.append(f"{relpath.as_posix()}:personal-email")
    if PRIVATE_LINKEDIN_RE.search(serialized):
        violations.append(f"{relpath.as_posix()}:linkedin-profile")


def main() -> int:
    raw_hashes = os.environ.get("RUMBO_PRIVACY_DENY_HASHES", "")
    deny = {h.strip().lower() for h in raw_hashes.split(",") if h.strip()}
    if not deny:
        print("PRIVACY_GATE_FAIL: private deny-hash set is missing")
        return 2
    if any(not re.fullmatch(r"[0-9a-f]{64}", h) for h in deny):
        print("PRIVACY_GATE_FAIL: deny-hash set is malformed")
        return 3

    violations: list[str] = []
    commit_ref = os.environ.get("RUMBO_PRIVACY_COMMIT_SHA", "HEAD")
    base_ref = os.environ.get("RUMBO_PRIVACY_BASE_SHA") or None

    for commit in new_commits(commit_ref, base_ref):
        validate_commit_metadata(commit, violations)

    for path in tracked_files():
        relpath = path.relative_to(ROOT)
        text = text_of(path)
        if text is None:
            continue
        if relpath in PUBLIC_PLUGIN_METADATA:
            validate_public_plugin_metadata(relpath, text, violations)
            continue
        if any(sha(candidate) in deny for candidate in candidates(text)):
            violations.append(relpath.as_posix())

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    founder = re.search(r"(?ms)^## Founder\s*$\s*^([^\r\n]+)", readme)
    if not founder or founder.group(1).strip() != PUBLIC_NAME:
        violations.append("README.md:founder-attribution")

    index = (ROOT / "index.html").read_text(encoding="utf-8")
    footer = re.search(r"Fundador:\s*([^<]+)", index)
    if not footer or footer.group(1).strip() != PUBLIC_NAME:
        violations.append("index.html:founder-attribution")

    if violations:
        print(f"PRIVACY_GATE_FAIL: {len(violations)} public-surface violation(s)")
        for item in sorted(set(violations)):
            print(f"VIOLATION_FILE={item}")
        return 1

    print("PRIVACY_GATE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
