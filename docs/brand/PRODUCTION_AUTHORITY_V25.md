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

Current social/profile reconciliation is governed by `SOCIAL_AUTHORITY_V25.md` and `distribution_lock_v2.json`. Historical V24/v1 compatibility state remains evidence only and does not override fresh provider readback.

## Current social boundary

Social/profile state was refreshed on 2026-10-02 and is subordinate to the production authority decision above.

- X: binding/publish authority PASS; handle `@RumboAGI`; display-name drift remains `RUMBO AGI`.
- YouTube: binding/publish authority PASS; public display `RUMBO IA` / handle `@rumboagi` is aligned.
- LinkedIn company: provider readback proves administered page `RUMBO IA`, `urn:li:organization:145014017`; founder personal LinkedIn remains a separate identity.
- TikTok, Instagram, Threads and Bluesky remain bound for publication but have explicit display/profile drift recorded in `SOCIAL_AUTHORITY_V25.md`.

Publication authority is not profile-edit authority. Current connected publishing tools expose no supported safe display-name/avatar writer for the drifted surfaces.

## Invariant

`MAIN_ADVANCE != PRODUCTION_AUTHORITY`.

A future production application/deployment may supersede this lock only through an explicit owner-authorization receipt in canonical issue #72 (or an explicitly superseding canonical registry), followed by exact deployment readback.

## Safety / spend

No credential extraction, cookie/storage extraction, force push, rule weakening, test social post, paid action, or production mutation was used in this arbitration. Spend: USD 0.
