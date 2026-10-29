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