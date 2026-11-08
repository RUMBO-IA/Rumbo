"""Read-only attestation of historic PUBLIC privacy metadata ref reachability.

A previously confirmed bad ref cannot be declared cleaned until both its
remote tip and its ancestry have been independently reconciled. The utility
never alters Git refs, branch protections, CI, or merge state.
"""
from __future__ import annotations

import re
from typing import Any

_SHA = re.compile(r"^[0-9a-f]{40}$")
_HEAD = "refs/remotes/origin/"
_PR_HEAD = re.compile(r"^refs/remotes/public-pr-head/([1-9][0-9]*)$")
_PR_MERGE = re.compile(r"^refs/remotes/public-pr-merge/([1-9][0-9]*)$")


def remote_ref(local_ref: str) -> str | None:
    """Convert the exact R2 local reference naming convention to GitHub refs."""
    if not isinstance(local_ref, str):
        return None
    if local_ref.startswith(_HEAD):
        suffix = local_ref[len(_HEAD):]
        if suffix and not suffix.startswith("/") and ".." not in suffix and "\\" not in suffix:
            return "refs/heads/" + suffix
        return None
    m = _PR_HEAD.fullmatch(local_ref)
    if m:
        return f"refs/pull/{m.group(1)}/head"
    m = _PR_MERGE.fullmatch(local_ref)
    if m:
        return f"refs/pull/{m.group(1)}/merge"
    return None


def parse_ls_remote(text: str) -> dict[str, str]:
    """Parse only proper SHA-tab-ref lines, rejecting duplicate refs."""
    if not isinstance(text, str):
        raise ValueError("remote ref data must be text")
    result: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 2 or not _SHA.fullmatch(fields[0]) or not fields[1].startswith("refs/"):
            raise ValueError("remote ref line malformed")
        sha, ref = fields
        if ref in result:
            raise ValueError("duplicate remote ref")
        result[ref] = sha
    return result


def reconcile(
    expected_bad: dict[str, set[str]],
    local_tips: dict[str, str],
    remote_tips: dict[str, str],
    observed_bad: dict[str, set[str]],
) -> dict[str, Any]:
    """Return BLOCKED_EXTERNAL only if every historical ref is unchanged and verified.

    A moved/deleted ref is UNRESOLVED, not CLEAN. A missing or mismatched Git
    ancestry is also UNRESOLVED; owner-governed remediation remains required.
    """
    rows: list[dict[str, Any]] = []
    valid = bool(expected_bad)
    for local_ref, expected in sorted(expected_bad.items()):
        remote = remote_ref(local_ref)
        local_tip = local_tips.get(local_ref)
        actual_tip = remote_tips.get(remote) if remote else None
        ancestry = observed_bad.get(local_ref)
        expected_valid = (
            isinstance(expected, (set, frozenset)) and bool(expected)
            and all(isinstance(x, str) and _SHA.fullmatch(x) for x in expected)
        )
        exact = (
            remote is not None and expected_valid
            and isinstance(local_tip, str) and _SHA.fullmatch(local_tip)
            and isinstance(actual_tip, str) and _SHA.fullmatch(actual_tip)
            and actual_tip == local_tip
            and isinstance(ancestry, (set, frozenset))
            and ancestry == expected
        )
        if not exact:
            valid = False
        rows.append({
            "local_ref": local_ref,
            "remote_ref": remote,
            "local_snapshot_tip": local_tip,
            "live_remote_tip": actual_tip,
            "exact_tip_match": bool(local_tip and actual_tip and local_tip == actual_tip),
            "exact_bad_commit_containment": bool(ancestry == expected and expected_valid),
            "expected_bad_commits": len(expected) if isinstance(expected, (set, frozenset)) else None,
            "observed_bad_commits": len(ancestry) if isinstance(ancestry, (set, frozenset)) else None,
            "verified": bool(exact),
            "category": (
                "BRANCH" if remote and remote.startswith("refs/heads/") else
                "GITHUB_MANAGED_PR" if remote and remote.startswith("refs/pull/") else
                "UNRECOGNIZED"
            ),
        })
    return {
        "classification": "BLOCKED_EXTERNAL" if valid else "UNRESOLVED",
        "verified_ref_count": sum(bool(row["verified"]) for row in rows),
        "contaminated_ref_count": len(rows),
        "unresolved_ref_count": sum(not row["verified"] for row in rows),
        "merge_authorized": False,
        "rows": rows,
        "next_safe_action": (
            "Owner-governed historical reference remediation with preservation of evidence. "
            "Do not delete GitHub-managed PR refs or weaken privacy scanning."
        ),
    }
