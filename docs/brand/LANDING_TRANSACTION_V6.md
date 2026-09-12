# RUMBO Brand V6 landing transaction

Status: CANDIDATE / NOT REFERENCED.

Canonical authority: issue #72.
Canonical target branch: feat/rumbo-brand-system-v1.
Expected parent commit before landing: 8587d54e2cd95ff881f817542646ce30b3ff4857.
Candidate tree: to be filled from Git tree readback after materialization.

Required author/committer identity must satisfy the active trusted Git metadata ruleset. No bypass, rule weakening, force update, production deployment, or main-branch mutation is authorized by this transaction.

Landing protocol:
1. Re-read canonical branch head and require exact match with expected parent.
2. Re-read candidate tree and required blob SHAs.
3. Create exactly one commit with the approved identity, expected parent, and candidate tree.
4. Fast-forward only feat/rumbo-brand-system-v1; force=false.
5. Read back branch head and commit tree; require exact equality.
6. Require Brand Contract CI to run against exact PR head SHA.
7. Run/inspect privacy, commercial coherence, security-header and brand gates required by repository governance.
8. Open or update the Brand PR only after the referenced candidate exists.
9. Resolve review threads and required reviews/statuses.

Fail closed on parent drift, identity mismatch, tree mismatch, CI ambiguity, unresolved review gates, or missing publication/production authority.

Invariant: OBJECT_MATERIALIZED != COMMIT_CREATED != BRANCH_REFERENCED != CI_PASS != REVIEW_PASS != PUBLICATION_AUTHORITY != PRODUCTION_DEPLOYMENT.
