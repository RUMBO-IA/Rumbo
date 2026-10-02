# RUMBO IA Social Authority V24

> Compatibility filename retained. Current reconciliation: 2026-10-02.
> Fresh authenticated/provider readback supersedes older observations stored under this path.

Status: SOCIAL_AUTHORITY_PARTIAL_PROFILE_ALIGNMENT

## Fresh verified channel state

| Channel | Binding / publish authority | Profile alignment | Readback |
| --- | --- | --- | --- |
| YouTube | PASS — connected as `RUMBO IA` / `@rumboagi` | PASS — display name aligned | PASS — authenticated provider readback |
| LinkedIn company | PASS — `urn:li:organization:145014017` / `RUMBO IA` | PASS — company display aligned | PASS — provider page readback; 2 followers observed |
| LinkedIn founder | PASS — `Sebastián Federico` | PERSONAL — separate founder authority | PASS — authenticated provider readback |
| X | PASS — handle `@RumboAGI` | DRIFT — display name `RUMBO AGI` | PASS — authenticated provider readback |
| TikTok | PASS — `rumboai` | DRIFT — handle-derived display | PASS — authenticated provider readback |
| Instagram | PASS — `rumbo.ia` | DRIFT — handle-derived display | PASS — authenticated provider readback |
| Threads | PASS — `rumbo.ia` | DRIFT — founder display `Sebastian Federico` | PASS — authenticated provider readback |
| Bluesky | PASS — `rumboia.bsky.social` | DRIFT — address-style display | PASS — authenticated provider readback |
| Facebook | PASS — founder account connected | NOT_COMPANY_SURFACE | PASS — account readback; no publishable company page proven |
| Pinterest | PASS — `fedesebasc` | NOT_CANONICAL_COMPANY_IDENTITY | PASS — authenticated provider readback |

All listed Upload-Post connections reported `reauth_required=false` in the 2026-10-02 reconciliation.

## Profile-edit authority boundary

Publication authority is not profile-edit authority.

Current connected publishing tools expose post publication/readback, but no supported safe writer for display-name/bio/avatar mutation on X, TikTok, Instagram, Threads or Bluesky. Therefore those drifts remain explicit.

`PROFILE_EDIT_BLOCKED_BY_TOOLING`

Do not fabricate alignment and do not use browser/OAuth mutation from the automated marketing watcher.

## Public naming law

- Company display name: `RUMBO IA`.
- Positioning: `Operational AI Systems`.
- Handles are addresses, not alternate brand names.
- Founder identity remains separate.
- `RUMBO AGI`, `rumboai`, `rumbo.ia` and `rumboia.bsky.social` are not approved display-name substitutes.

## Logo/avatar boundary

Canva Brand Board `DAHWsPbUL-U` and candidate packs remain design candidates.

`LOGO_CANDIDATE != PUBLIC_AVATAR_PROMOTED`

No profile is considered visually aligned merely because a candidate logo exists.

## Production boundary

Social/profile authority is independent of web-production authority.

The canonical domain remains governed by issue #72 and `production_lock_v1.json`. Social alignment does not authorize Vercel alias, DNS or production deployment changes.

## Safety / spend

- credential extraction: NO
- cookie/storage extraction: NO
- browser/OAuth profile mutation: NO
- social test post as authority probe: NO
- paid action: NO
- external spend: USD 0
