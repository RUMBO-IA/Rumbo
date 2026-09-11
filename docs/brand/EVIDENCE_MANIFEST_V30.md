# RUMBO IA Evidence Manifest V30

Observed: 2026-09-11
Status: CURRENT_RECONCILED_EVIDENCE

## Authority hierarchy

1. Canonical registry: `RUMBO-IA/Rumbo#72`.
2. Production binding: `docs/brand/production_lock_v1.json`.
3. This manifest summarizes current proven state; it does not override #72 or the production lock.
4. Earlier evidence manifests and receipts remain historical evidence, not current authority when they conflict with this state.

## Canonical identity

- public master brand: `RUMBO IA`
- technical/internal namespace: `RUMBO`
- public descriptor: `Human-controlled AI CRM and automation for small businesses in Latin America.`
- first public mention rule: use `RUMBO IA`; use `RUMBO` only after identity is established.

## Repository state

- repository: `RUMBO-IA/Rumbo`
- reconciled main SHA before this documentation change: `fabb3a53b82e947186a3fe195e9d9b06a3332c10`
- Brand Contract: PASS
- Public Privacy gate: PASS
- production surface watch: PASS
- production watch first real run: `34588629746` / SUCCESS

## Authorized production

- domain: `rumbo.verso.fans`
- application SHA: `34c625c65e047fdec06a5bef7064d2de6bed48ba`
- deployment: `dpl_8KbqvsKuua22xK4EQYZmtF3KXmNK`
- deployment state: `READY`
- deployment target: `production`
- normalized public/source bytes: `21535`
- normalized public/source SHA-256: `35129b1068ebe800bfcc3fd5ad0ad12908077494d7e6c11759c4d20263074625`
- invariant: `MAIN_ADVANCE != PRODUCTION_AUTHORITY`

## Social authority

- X: `@RumboAGI`; binding/publish authority PASS; fresh connector metadata reports display name `RUMBO AGI`, conflicting with the V24 public-UI receipt `RUMBO IA`; current profile alignment is NOT_PROVEN pending readback.
- YouTube: `RUMBO IA / @RumboAGI`; binding/publish authority PASS; canonical description PASS.
- LinkedIn: personal profile binding PASS; no administered RUMBO IA company page is proven.
- full cross-channel profile alignment: NOT_PROVEN.

## Supersession / negative knowledge

`docs/brand/EVIDENCE_MANIFEST_V1.md` describes an earlier pre-landing candidate state and MUST NOT be used as current operational status. Its immutable historical facts remain useful, but its candidate/production assertions are superseded by #72, V25, the production lock, V28 live verification and V29 scheduled surface watch.

No production alias change, social test post, credential extraction, rule weakening or paid action is authorized by this manifest.

## Current gate

`BRAND_CONTROL_PLANE=PASS`
`AUTHORIZED_PRODUCTION_CURRENT=PASS`
`PRODUCTION_SURFACE_WATCH=PASS`
`SOCIAL_AUTHORITY=PARTIAL_PROFILE_ALIGNMENT_WITH_X_METADATA_CONFLICT`
`FULL_DISTRIBUTION_PASS=NO`
`SPEND_USD=0`

Next transition: resolve the X display-name conflict through an authorized public/profile readback or profile-edit surface. LinkedIn company-page absence remains a separate gate. Do not manufacture a new version solely to restate unchanged state.
