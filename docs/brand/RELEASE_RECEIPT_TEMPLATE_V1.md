# RUMBO IA Brand Release Receipt Template V1

Status: TEMPLATE

## Identity
- Brand system version: `V1`
- Candidate branch: `<branch>`
- Exact head SHA: `<sha>`
- Candidate tree SHA: `<tree_sha>`
- Author email: `<author_email>`
- Committer email: `<committer_email>`

## Evidence
- Brand contract verifier: `<PASS|FAIL>`
- Unit tests: `<PASS|FAIL>`
- Exact-head CI run: `<url/id>`
- Review threads resolved: `<PASS|FAIL>`
- Required approvals: `<count/status>`
- Claim audit: `<PASS|FAIL>`
- Channel consistency audit: `<PASS|FAIL>`

## Authority
- Publication authority: `<AUTHORIZED|NOT_AUTHORIZED>`
- Production deployment authority: `<AUTHORIZED|NOT_AUTHORIZED|NOT_APPLICABLE>`
- Authority evidence: `<pointer>`

## Immutable artifact digests
Record path → blob SHA for every Brand V1 governed file included in the release.

## Decision
- `BRAND_SPEC_PASS=<...>`
- `CI_PASS=<...>`
- `REVIEW_PASS=<...>`
- `PUBLICATION_AUTHORITY=<...>`
- `PRODUCTION_DEPLOYMENT=<...>`

No field may be inferred from another. Missing evidence fails closed.
