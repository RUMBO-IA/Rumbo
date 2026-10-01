# RUMBO IA Production Promotion Candidate — 2026-10-01

Status: CANDIDATE / NO_GO_PENDING_EXPLICIT_PRODUCTION_AUTHORITY

## Exact candidate
- Source SHA: `68c633a19c0db72038c1436e5efa0ad53d162e95`
- Source branch at observation: `main`
- Vercel preview: `dpl_3PEs1WgST84RmiKnCsd1B2wztLGT`
- Preview state: `READY`
- Preview root readback: HTTP 200
- Exact-head `Public privacy gate`: SUCCESS
- Exact-head `Vercel`: SUCCESS

## Why this candidate
- Current production is still bound to `34c625c65e047fdec06a5bef7064d2de6bed48ba` and serves the older CRM/SMB narrative.
- The candidate root presents the governed Operational AI positioning: Revenue Recovery, Agent Reliability and Guardian.
- The candidate tree contains `privacy.html`, `terms.html` and `styles.css`, closing the three SOURCE_MISSING conditions seen on the current production SHA.
- The candidate also contains the governed security surface.

## Current production
- Deployment: `dpl_8KbqvsKuua22xK4EQYZmtF3KXmNK`
- Application SHA: `34c625c65e047fdec06a5bef7064d2de6bed48ba`
- State: `READY`
- Classification: SERVING / LEGACY_POSITIONING / PROVENANCE_DRIFT

## Relationship to PR #182
- PR #182 reconstructs the old production application reproducibly.
- That remains useful forensic/provenance evidence.
- It is NOT the preferred future brand-production candidate because it intentionally preserves the legacy CRM/SMB application.
- This receipt identifies current `main` as the stronger technical candidate for any future production-promotion decision.

## Gates
- Source/runtime privacy gate: PASS
- Vercel build/deploy gate: PASS
- Preview root readback: PASS
- Legal/style source presence: PASS
- Full protected-preview clean-URL readback for `/privacy`, `/terms`, `/security`: NOT_PROVEN_AUTH_GATE
- Explicit human production-promotion authority: NOT_PRESENT
- Production alias mutation: NOT_EXECUTED

## Invariants
- `TECHNICAL_CANDIDATE != PRODUCTION_AUTHORITY`
- `CI_PASS != PUBLICATION_RECEIPT`
- `PREVIEW_READY != PRODUCTION_GO`
- `DIRECT_MAIN_WRITE=NO`
- `PRODUCTION_PROMOTION=NO_GO`
- `NEW_EXTERNAL_SPEND_USD=0`

## Next safe action
Obtain explicit production-promotion authority binding this exact candidate SHA and deployment target, then perform the alias promotion with immediate remote readback and rollback receipt. Do not infer that authority from this receipt.
