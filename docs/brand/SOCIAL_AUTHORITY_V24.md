# RUMBO IA Social Authority V24

Observed: 2026-09-11
Status: SOCIAL_AUTHORITY_PASS_PROFILE_ALIGNMENT_PARTIAL_PRODUCTION_HOLD

## Verified channel state

| Channel | Binding / publish authority | Profile alignment | Readback |
| --- | --- | --- | --- |
| X | PASS — `@RumboAGI` | PASS — display name `RUMBO IA`; canonical short bio applied | PASS — public profile + historical media/analytics |
| YouTube | PASS — `RUMBO IA` / `@RumboAGI` | PASS — canonical channel description published | PASS — public channel + analytics |
| LinkedIn | PASS — personal profile `Sebastián Federico`; reauth complete | COMPANY_SURFACE_NOT_PRESENT | LIMITED_BY_PLATFORM — personal analytics/posts not exposed by LinkedIn API |

## Authority boundaries

Publication authority is not profile-edit authority. No social post was created as an authority test. X and YouTube were aligned through their official profile UIs and read back publicly. The connected LinkedIn identity is a personal profile, while the canonical LinkedIn copy is company/about copy; no RUMBO IA company page is administered by the connected account, so that copy was not applied to the personal profile.

## Production reconciliation

Git `main` records V22 as the intended production application, but `rumbo.verso.fans` is currently bound to an older V16 deployment after a separate concurrent execution explicitly promoted that artifact. Production alias mutation is therefore frozen in this lane until cross-lane authority is reconciled.

`PRODUCTION_RECONCILIATION=HOLD_CROSS_LANE_CONFLICT`

## Safety / spend

- credential extraction: NO
- cookie/storage extraction: NO
- security bypass: NO
- social test post: NO
- paid action: NO
- spend: USD 0

## Promotion invariant

Do not report full profile alignment while the LinkedIn company surface is absent. Do not change the production alias from this lane while the cross-lane production conflict remains unresolved.
