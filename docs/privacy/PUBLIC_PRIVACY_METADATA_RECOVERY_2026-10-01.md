# Public privacy metadata recovery — 2026-10-01

## Incident

GitHub PR #180 was integrated through GitHub's server-side rebase path.
The source commit used repository-approved GitHub noreply metadata, but GitHub
created public main commit:

7734270af5e1928215838fb0f0aee940599d43e4

with committer metadata that matches values intentionally denied by the public
privacy gate.

## Why this is not rewritten

The commit is already part of public main history. Removing it would require a
non-fast-forward rewrite of protected public history. That would disrupt commit
and PR lineage and violate the repository's non-fast-forward governance.

## Bounded remediation

The verifier therefore carries one exact-SHA, exact-field exception for:
- committer-name
- committer-email

It does not:
- expose the denied raw values in source;
- exempt author metadata;
- exempt file content;
- change the deny-hash secret;
- disable all-ref scanning;
- authorize any future commit with the same metadata;
- authorize force pushes or history rewrites.

Future integration for privacy-sensitive branches must promote the exact
already-checked commit by fast-forward. Do not use a server merge mode that
rewrites the committer identity.

LEGACY_EXCEPTION != FUTURE_AUTHORIZATION
CHECKED_HEAD != SERVER_REWRITTEN_COMMIT
