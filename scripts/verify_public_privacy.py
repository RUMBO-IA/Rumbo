import hashlib
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NAME = "Sebastián"
APPROVED_NAMES = {PUBLIC_NAME, "fscfede-beep", "RUMBO Privacy Automation"}
APPROVED_AUTHOR_EMAILS = {
    "sebastian@rumbo.verso.fans",
    "293577326+fscfede-beep@users.noreply.github.com",
    "41898282+github-actions[bot]@users.noreply.github.com",
}
APPROVED_COMMITTER_EMAILS = APPROVED_AUTHOR_EMAILS | {"noreply@github.com"}
APPROVED_PUBLIC_TEXT_EMAILS = APPROVED_COMMITTER_EMAILS
EMAIL_RE = re.compile(r"(?i)(?<![a-z0-9._%+-])[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,63}(?![a-z0-9._%+-])")


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


def email_candidates(text: str):
    yield from EMAIL_RE.findall(text)


def is_denied(value: str, deny: set[str]) -> bool:
    return sha(value) in deny


def text_has_denied_value(text: str, deny: set[str]) -> bool:
    return any(is_denied(value, deny) for value in candidates(text)) or any(
        is_denied(email, deny) for email in email_candidates(text)
    )


def text_has_unapproved_email(text: str) -> bool:
    return any(email not in APPROVED_PUBLIC_TEXT_EMAILS for email in email_candidates(text))


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
    if author_name not in APPROVED_NAMES or is_denied(author_name, deny):
        violations.append("git:head-author-name")
    if author_email not in APPROVED_AUTHOR_EMAILS or is_denied(author_email, deny):
        violations.append("git:head-author-email")
    if committer_email not in APPROVED_COMMITTER_EMAILS or is_denied(committer_email, deny):
        violations.append("git:head-committer-email")
    for path in tracked_files():
        text = text_of(path)
        if text is None:
            continue
        relpath = path.relative_to(ROOT).as_posix()
        if text_has_unapproved_email(text):
            violations.append(f"{relpath}:unapproved-email")
        if text_has_denied_value(text, deny):
            violations.append(f"{relpath}:denied-value")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    founder = re.search(r"(?ms)^## Founder\s*$\s*^([^\r\n]+)", readme)
    if not founder or founder.group(1).strip() != PUBLIC_NAME:
        violations.append("README.md:founder-attribution")

    index = (ROOT / "index.html").read_text(encoding="utf-8")
    footer = re.search(r"Fundador:\s*([^<]+)", index)
    if not footer or footer.group(1).strip() != PUBLIC_NAME:
        violations.append("index.html:founder-attribution")

    landing_en = (ROOT / "apps/landing-publica/index-en-openai.html").read_text(encoding="utf-8")
    landing_founder = re.search(r"RUMBO IA is developed by\s+([^<\r\n]+)", landing_en)
    if not landing_founder or landing_founder.group(1).strip() != PUBLIC_NAME:
        violations.append("apps/landing-publica/index-en-openai.html:founder-attribution")

    if violations:
        print(f"PRIVACY_GATE_FAIL: {len(violations)} public-surface violation(s)")
        for item in sorted(set(violations)):
            print(f"VIOLATION_FILE={item}")
        return 1

    print("PRIVACY_GATE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
