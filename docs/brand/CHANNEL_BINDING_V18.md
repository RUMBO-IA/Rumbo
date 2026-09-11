# RUMBO IA Channel Binding V18

Observed: 2026-09-11
Status: PARTIAL_PASS

## Authority model

RUMBO IA separates profile-identity authority from publication authority. A channel may allow publishing while still denying profile bio/name edits.

## Verified bindings

| Channel | Account / handle | Publish authority | Profile-edit authority | Readback |
| --- | --- | --- | --- | --- |
| YouTube | RUMBO IA / `@rumboagi` | PASS | NOT_EXPOSED_BY_CONNECTED_TOOLS | PASS |
| LinkedIn | Sebastián Federico | REAUTH_REQUIRED | NOT_PROVEN | FAIL_CLOSED |
| X | `@RumboAGI` canonical target | NOT_CONNECTED | NOT_PROVEN | FAIL_CLOSED |
| Metricool | brand `6769976` | NO_NETWORKS_CONNECTED | N/A | PASS |

## YouTube evidence

Connected profile `rumboia` exposes YouTube as `RUMBO IA` / `@rumboagi`. The connected account can read published media and analytics. Public video `kXE1QMNaeyM` is readable through the authenticated integration.

## External blockers

- LinkedIn session is expired and requires explicit reauthorization by the user.
- X has no connected account in Upload-Post or Metricool.
- Connected tools do not expose channel bio/profile-description mutation for YouTube, LinkedIn or X.

## Canonical pending profile copy

X: Human-controlled AI CRM + automation for LATAM small businesses. CRM, opportunities, revenue recovery and reliability controls.

LinkedIn: use `docs/brand/PROFILE_COPY_V1.md` company/about copy.

YouTube: use `docs/brand/PROFILE_COPY_V1.md` channel-description copy.

## Promotion invariant

`DISTRIBUTION=PASS` requires, per populated external channel: authenticated write authority for the intended surface, canonical copy applied, readback, and claim-state review. Publication authority alone MUST NOT be reported as profile-edit authority.