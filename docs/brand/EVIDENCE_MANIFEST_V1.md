# RUMBO Brand Evidence Manifest V1

> **Historical manifest.** Current operational evidence is reconciled in `EVIDENCE_MANIFEST_V30.md`. This V1 file preserves pre-landing evidence and MUST NOT be interpreted as current production or distribution state.

Status: CANDIDATE / NOT YET BRANCH-REFERENCED

## Base authority
- repository: `RUMBO-IA/Rumbo`
- feature branch: `feat/rumbo-brand-system-v1`
- reconciled branch head: `8587d54e2cd95ff881f817542646ce30b3ff4857`
- previous extended candidate tree: `6e56a4a0f9018a5987d8db18347c7f147b469167`

## Reconciliation correction
The earlier Brand Gate static assessment was incomplete. Repository evidence proves both a root public surface and `apps/landing-publica/` candidate surfaces exist. The audited live production site matches root `index.html`; `apps/landing-publica/README.md` previously called its own `index.html` the principal public landing, creating an authority/brand-drift ambiguity.

The corrected candidate therefore:
1. keeps root `index.html` as the currently reconciled canonical visual surface;
2. classifies `apps/landing-publica/` as secondary/candidate until a separate publication receipt promotes it;
3. expands the verifier to check identity, human-control language and unsupported claims across all public HTML variants;
4. expands CI path filters to include root `index.html`, root `README.md`, and `apps/landing-publica/**`;
5. preserves canonical V1 palette enforcement on the currently audited root surface rather than silently accepting a second palette as canonical.

## Corrected immutable objects
- `docs/brand/BRAND_SYSTEM_V1.md` -> `aeb07c83620a5a58792da74673edb8b7188c8c02`
- `apps/landing-publica/README.md` -> `e3be39a9222a4b9daec68b7289ef6b8c909f3de4`
- `scripts/verify_brand_contract.py` -> `30ee397d9f572e3c9afd6759535ab96aa8b7209a`
- `scripts/test_verify_brand_contract.py` -> `8305e3d6ff084fe8bedc7ddd29d28c011a081356`
- `.github/workflows/brand-gate.yml` -> `afd1efc749b6d60f4a68f7968661fea1b9e41d5f`

## Evidence states
Proven from repository/live evidence:
- canonical name RUMBO IA on root and alternate surfaces;
- root surface uses Brand V1 palette;
- live site exposes human-control positioning and demonstration labeling;
- README separates `main` from production;
- active Git metadata ruleset remains enforced with no bypass actors.

Not proven until separately executed:
- corrected candidate branch reference;
- exact-head CI PASS;
- governed runtime test PASS;
- review/approval PASS;
- publication authority;
- production deployment.

Invariant:
`OBJECT_MATERIALIZED != BRANCH_REFERENCED != TEST_PASS != CI_PASS != REVIEW_PASS != PUBLICATION_AUTHORITY != PRODUCTION_DEPLOYMENT`
