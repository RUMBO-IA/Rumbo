# Fork contribution and promotion protocol

Status: fail-closed design for the future `RUMBO-IA/rumbo-open-lab`.

## 1. Two trust stages

External code and accepted integration candidates are different objects.

`FORK_PROPOSAL != INTERNAL_ACCEPTANCE_CANDIDATE`

Stage A — fork proposal:
- contributor-owned fork and branch;
- no organization membership required;
- `pull_request` CI only;
- read-only `GITHUB_TOKEN`;
- no repository or organization secrets;
- GitHub-hosted ephemeral runner or contributor-owned sandbox only;
- no production data or credentials;
- no self-hosted RUMBO runner;
- no deployment authority.

Stage B — internal acceptance candidate:
- created by a maintainer only after scope, license/inbound terms, authorship/right-to-submit, and review are satisfied;
- rematerialize or cherry-pick only the reviewed file/content delta into an internal RUMBO branch;
- preserve an approved Git identity;
- rerun canonical secret-backed/privacy/security checks on the exact internal SHA;
- require normal review and protected-branch rules;
- integration remains separate from deployment and production authorization.

A green fork CI run is never accepted as the canonical privacy/security attestation for promotion.

## 2. Fork CI rules

GitHub documents that workflows triggered by `pull_request` from forks receive a read-only token, do not receive normal repository/organization secrets, and may require maintainer approval before running.

Open Lab fork CI must therefore:
- declare explicit `permissions: contents: read` or narrower;
- pin third-party actions to full commit SHAs;
- use `persist-credentials: false` when checking out untrusted code;
- avoid write permissions and OIDC;
- avoid caches or artifacts that later privileged workflows trust without revalidation;
- avoid executing untrusted code on persistent/self-hosted infrastructure;
- use synthetic fixtures and public dependencies only.

## 3. Privileged event rule

Prefer `pull_request` for untrusted test execution.

A `pull_request_target`, `workflow_run`, or `issue_comment` workflow may perform metadata-only automation when necessary, but it must never fetch, checkout, source, install, build, test, or otherwise execute contributor-controlled code or artifacts while privileged.

Privileged workflows must use the minimum token permission and must treat titles, branch names, PR bodies, comments, filenames, artifacts, and API-returned contributor content as untrusted input.

## 4. First-time contributor workflow approval

When GitHub requires approval before running a public fork workflow, a maintainer reviews the diff first—especially changes to `.github/workflows/`, build/install scripts, dependency manifests, package-manager hooks, and generated artifacts—then approves the workflow only if running it on isolated GitHub-hosted compute is acceptable.

Approval to run CI is not code acceptance.

## 5. Protected paths

External Open Lab proposals that modify authority-bearing surfaces require maintainer rematerialization and focused review. Examples:
- `.github/workflows/**`;
- `.github/CODEOWNERS`;
- security policy or disclosure routes;
- release/publishing configuration;
- deployment configuration;
- dependency or package-manager hooks;
- repository governance and contributor-license machinery.

The public product front door `RUMBO-IA/Rumbo` is stricter: non-collaborators use Issues/proposals rather than an external product-code merge path.

## 6. Secrets and privacy

A secret-backed RUMBO privacy gate cannot be made equivalent on an untrusted fork by substituting an empty or public value for the secret.

If a canonical check requires a private deny-set, credential, signing key, release token, or other secret, that check runs only after the reviewed contribution has crossed into an internal acceptance candidate.

Missing secrets on the fork stage are a trust-boundary fact, not a reason to expose the secret or weaken the canonical check.

## 7. Cost boundary

Fork CI and sandboxes must not create RUMBO-funded spend by default.

Prefer:
1. contributor local Dev Container;
2. contributor DevPod/local Docker;
3. contributor personal included Codespaces allowance;
4. GitHub-hosted public-repository CI where included;
5. explicit owner-approved resources only when the incremental cost is proven acceptable.

## 8. Promotion invariant

`PROPOSED != CI_PASSED != REVIEWED != RIGHTS_CLEARED != ACCEPTED != INTERNALIZED != CANONICAL_CHECKS_PASSED != MERGED != DEPLOYED != PRODUCTION_AUTHORIZED`

Every transition needs its own evidence.
