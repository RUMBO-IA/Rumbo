import hashlib
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NAME = "Sebastián Federico"


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

    # Prevent accidental publication of personal commit metadata on new heads.
    commit_ref = os.environ.get("RUMBO_PRIVACY_COMMIT_SHA", "HEAD")
    author_name = subprocess.check_output(["git", "show", "-s", "--format=%an", commit_ref], cwd=ROOT, text=True).strip()
    author_email = subprocess.check_output(["git", "show", "-s", "--format=%ae", commit_ref], cwd=ROOT, text=True).strip()
    committer_email = subprocess.check_output(["git", "show", "-s", "--format=%ce", commit_ref], cwd=ROOT, text=True).strip()
    approved_names = {PUBLIC_NAME, "fscfede-beep"}
    approved_emails = {"sebastian@rumbo.verso.fans", "293577326+fscfede-beep@users.noreply.github.com"}
    if author_name not in approved_names:
        violations.append("git:head-author-name")
    if author_email not in approved_emails:
        violations.append("git:head-author-email")
    committer_is_approved = committer_email in approved_emails or committer_email == "noreply@github.com"
    if not committer_is_approved:
        violations.append("git:head-committer-email")
    for path in tracked_files():
        text = text_of(path)
        if text is None:
            continue
        if any(sha(candidate) in deny for candidate in candidates(text)):
            violations.append(path.relative_to(ROOT).as_posix())

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