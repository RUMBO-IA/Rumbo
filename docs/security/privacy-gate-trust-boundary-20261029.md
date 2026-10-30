# Privacy gate trust boundary — 2026-10-29

Status: CANDIDATE_ONLY / NO_MERGE / NO_DEPLOY.

## Risk
The public workflow checks out PR HEAD and executes scripts from it. A secret injected into that step can be read by candidate-controlled code. Disabling checkout credential persistence does not protect environment secrets.

## Implemented candidate
Ordinary pull_request tests run without RUMBO_PRIVACY_DENY_HASHES. The secret-dependent verifier runs only on a push to refs/heads/main. This is not complete private verification of PR candidates.

## Required before promotion
1. Run an independently trusted verifier on exact PR HEAD and private deny list, without executing candidate code.
2. Review protected verifier provenance and event permissions; a pull_request_target definition on an unmerged branch does not run as trusted base workflow.
3. Validate exact-SHA binding, missing-secret fail-closed behavior, fork and internal PR handling.
4. Audit hostile inputs: symlinks, large files, git metadata, Unicode, subprocesses and logs.
5. Obtain real trusted check results on exact HEAD and retain branch protection. No bypass, merge, deployment or spending.

## Same-repository PR caveat
A pull_request workflow from a branch within the same repository may access repository secrets. The static test checks only known YAML patterns; it does not enforce security against an author modifying other workflows. A protected environment with required approval and a trusted verifier are necessary before considering the private gate operational. GitHub repository administrators must confirm environment rules, branch rules, and required checks; no such settings have been verified or changed here.

## 2026-10-30 local correction: effective YAML condition
The old regression accepted an always() condition when the expected main/push guard appeared only in a comment. The validator now parses YAML with a string-scalar loader, rejects duplicate mapping keys and unsupported tags/anchors/aliases, and validates the effective step condition, secret environment assignment, exact push SHA and read-only token contract. This remains a conservative static contract test, not an independent private PR verifier.

Python 3.12 CI installs PyYAML 6.0.3 using pinned Linux x86_64 / Windows x86_64 wheel hashes from PyPI. The Node static pilot still introduces no root package.json or turbo.json. Other Python/platform combinations require a separately verified wheel hash.

Before public promotion, an approved independent verifier must still check the exact candidate commit without running candidate code under secrets. A successful public test job is not a private-policy attestation. No repository secret, environment protection, required check, Vercel account setting or production alias was changed by this local correction.
