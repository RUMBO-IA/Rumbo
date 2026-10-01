# Legacy commit-metadata exception — 2026-10-01

## Incident

GitHub PR #176 was merged through GitHub's rebase path. The resulting public
main commit is:

cb289031bb9e9808e8c168411ec9053f3325f0c0

The source commit used an approved GitHub noreply identity, but the server-side
rebase produced committer metadata that matches values intentionally denied by
the public privacy gate.

## Remediation decision

A protected-public-history rewrite would require a non-fast-forward rewrite of
main, disrupt existing PR/commit lineage, and violate the repository's current
non-fast-forward governance. The already-public metadata therefore cannot be
made non-public by an ordinary forward fix.

The privacy verifier now contains one exact-SHA, exact-field exception for:

- committer-name
- committer-email

on the commit above only.

This exception:

- does not expose the denied raw values in source;
- does not allow the same values on any other commit;
- does not exempt author metadata;
- does not exempt repository file contents;
- does not change the deny-hash secret;
- does not disable repository-wide metadata scanning;
- does not authorize force pushes or history rewrites.

## Prevention

Future release integration should prefer an exact checked commit whose
author/committer metadata already matches the public allowlist. Avoid
server-side merge modes that can rewrite committer identity to a denied account
email.

LEGACY_EXCEPTION != FUTURE_AUTHORIZATION
HISTORY_IMMUTABLE != PRIVACY_GATE_DISABLED
