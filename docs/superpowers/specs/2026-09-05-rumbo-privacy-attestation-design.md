# RUMBO Privacy Attestation — Design

Date: 2026-09-05
Status: Approved approach B; implementation not started
Repository: `RUMBO-IA/Rumbo`
Parent design: `docs/superpowers/specs/2026-09-05-rumbo-safe-merge-authority-design.md`

## Objective

Allow `RUMBO Safe Merge Authority` to prove the privacy gate for an exact candidate SHA without copying `RUMBO_PRIVACY_DENY_HASHES` from GitHub Actions to the authorized host.

The GitHub Actions privacy workflow remains the only component that receives the deny-hash secret. The host consumes a successful workflow run as a SHA-bound attestation and combines it with local Git ancestry and public commit-metadata checks.

## Security invariant

The deny-hash secret must never be exported, printed, copied to local environment variables, persisted in receipts, or passed to another service.

A missing, stale, ambiguous, failed, or workflow-drifted attestation must produce `SAFE_STOP` before any branch write.

## Trusted attestation identity

The attestation is valid only when all of these values match policy:

- repository: `RUMBO-IA/Rumbo`;
- workflow path: `.github/workflows/privacy-gate.yml`;
- workflow ID: `347174988`;
- event: `pull_request` for the requested PR;
- head SHA: exactly the requested candidate SHA;
- conclusion: `success`;
- workflow file Git blob: `3ab38299fd55f9182e9e10834b04550cc832557a`;
- workflow file SHA-256: `5dcc2a09e10173bb37de8d449b9105296eb8ec966c33946b9f0400b6e2f2ab99`.

The two workflow digests pin the reviewed workflow content. A future workflow change requires a separate review and explicit policy update before its runs can authorize G3.

## G3 composition

`PRIVACY_ANCESTRY` passes only when three proofs agree:

1. local Git proves the current target tip is an ancestor of the candidate;
2. local public metadata validation reports no author/committer violations for the candidate ancestry;
3. GitHub reports a successful pinned privacy workflow run for the exact PR and candidate SHA.

No one proof substitutes for another.

## Data flow

1. The authority reads PR identity and required checks for the expected head SHA.
2. It fetches remote refs and validates ancestry plus public Git metadata locally.
3. It reads the workflow file at the candidate SHA and verifies both pinned digests.
4. It lists `pull_request` runs for the pinned workflow, filters to the exact candidate SHA and requested PR, selects the newest matching run by `run_attempt` and creation time, and requires that run to be completed with conclusion `success`.
5. It records only non-secret evidence: workflow ID, run ID, event, conclusion, head SHA, PR number, workflow digests, and timestamps.
6. Only then may evaluation continue to `PRODUCTION_NO_GO` and `FAST_FORWARD_ONLY`.

## Fail-closed rules

Reject the attestation when any of these conditions occurs:

- no matching run exists for the exact SHA and PR;
- the newest matching run is not completed successfully;
- workflow ID or path differs from policy;
- workflow content differs from either pinned digest;
- run head SHA differs from the requested SHA;
- run is not associated with the requested PR;
- GitHub evidence cannot be read or parsed;
- local ancestry or metadata proof fails.

## Components and interfaces

`safe_merge_policy.py` gains immutable attestation policy fields for workflow ID, path, Git blob, SHA-256, and accepted event.

`safe_merge_evidence.py` gains read-only methods:

- `workflow_blob(candidate_sha: str) -> dict` with path and both digests;
- `privacy_attestation(pr_number: int, candidate_sha: str) -> dict` with normalized run evidence.

`safe_merge_authority.py` changes G3 so `privacy_ok()` no longer requires the deny-set on the host. Instead, G3 requires local metadata/ancestry plus `privacy_attestation()`.

Receipts add a `privacy_attestation` evidence block but never include environment values, logs containing masked secrets, or authorization material.

## GitHub evidence boundary

The authority may use only authenticated read operations to obtain workflow/run evidence. It must not rerun, cancel, dispatch, edit, or otherwise mutate Actions state as part of attestation.

The workflow run must already exist and be successful before the authority executes. Waiting for a pending run is allowed only as a bounded read loop with a hard timeout; timeout ends as `SAFE_STOP`.

## Non-goals

- No GitHub secret retrieval or replication.
- No new GitHub App, token, service, database, or signing infrastructure.
- No workflow self-modification.
- No automatic rerun of failed CI.
- No relaxation of metadata rules, branch rulesets, or main protection.
- No production deployment or traffic promotion.

## Testing strategy

Implementation follows red-green-refactor. Required tests cover:

- exact successful run is accepted;
- successful run for a different SHA is rejected;
- successful run for another PR is rejected;
- failed, cancelled, pending, or missing run is rejected;
- workflow ID/path mismatch is rejected;
- Git blob mismatch is rejected;
- SHA-256 mismatch is rejected;
- GitHub read failure is rejected;
- local metadata failure still rejects even when CI passed;
- local ancestry failure still rejects even when CI passed;
- receipt records attestation identifiers but contains no secret material.

A real dry-run against PR #41 must reach `DRY_RUN_PASS` without host access to `RUMBO_PRIVACY_DENY_HASHES`.

## Rollout and acceptance

Phase A: unit tests and regression suite only.

Phase B: real dry-run against PR #41, proving G1-G5 with no writes.

Phase C: temporary probe branches only. The authority must advance a probe base to the exact reviewed probe head by normal fast-forward, verify it, emit a digest-valid receipt, and remove every temporary remote ref afterward.

Phase D: audit readiness for `main`. This phase does not itself modify `main`; it proves the authority is ready for a separately authorized exact-SHA integration.

Acceptance requires all tests green, PR privacy/Vercel checks green, no secret copied to host, zero probe refs remaining, `main` unchanged during Phases A-C, and production live deployment unchanged.