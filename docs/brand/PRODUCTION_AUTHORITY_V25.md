# RUMBO IA Production Authority V25

Observed: 2026-09-11
Status: PRODUCTION_AUTHORITY_RECONCILED

## Authority decision

Canonical registry issue #72 controls brand publication and production authorization. Its owner-authorization receipt V43 explicitly authorizes production application SHA `34c625c65e047fdec06a5bef7064d2de6bed48ba` through Vercel deployment `dpl_8KbqvsKuua22xK4EQYZmtF3KXmNK` on `rumbo.verso.fans`.

Later #72 receipts V44/V45 classify post-V43 deployments, including `dpl_Dua7MUambPmzntbFhDCFEmNoQodT`, as production drift because no later owner-authorization receipt expanded the production binding.

## Reconciliation

- authorized production application: `34c625c65e047fdec06a5bef7064d2de6bed48ba`
- authorized production deployment: `dpl_8KbqvsKuua22xK4EQYZmtF3KXmNK`
- public surface: `rumbo.verso.fans`
- repository release posture: reconciled by PR #109
- production traffic mutation in V25: NONE; live traffic was already on the authorized deployment

Historical V22/V23 receipts remain immutable evidence of what those executions observed and did, but their claims that `dpl_Dua7MUambPmzntbFhDCFEmNoQodT` was the authorized production target are superseded by the higher-authority #72 registry record.

V24 social authority remains valid and is not superseded by this production arbitration.

## Current social boundary

- X: binding/publish authority PASS; public `RUMBO IA` / `@RumboAGI` profile copy PASS.
- YouTube: binding/publish authority PASS; public `RUMBO IA` / `@RumboAGI` canonical description PASS.
- LinkedIn: personal profile binding PASS; no administered RUMBO IA company page exists.

## Invariant

`MAIN_ADVANCE != PRODUCTION_AUTHORITY`.

A future production application/deployment may supersede this lock only through an explicit owner-authorization receipt in canonical issue #72 (or an explicitly superseding canonical registry), followed by exact deployment readback.

## Safety / spend

No credential extraction, cookie/storage extraction, force push, rule weakening, test social post, paid action, or production mutation was used in this arbitration. Spend: USD 0.
