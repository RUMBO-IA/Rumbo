# RUMBO IA — DevDay 2026 Marketing Campaign State R1

Observed: 2026-09-29 23:22 ART
Branch: campaign/devday-marketing-r1-20260929
Base: RUMBO-IA/Rumbo@b9c1a30a90408d299467b2c1eb3eb9ec475dd707
Status: CAMPAIGN_DRAFT_ONLY / ZERO_SPEND / PUBLIC_CLEANUP_PARTIAL_BY_TOOLING

## Scope
Marketing/viralization only: brand, DevDay/OpenAI editorial evidence, social distribution, lead capture, assets, conversion and campaign receipts.
This branch does not own control-plane, CI, Windows recovery, GovOps, billing or production promotion.

## Canon pointers
Brand authority stays on main:
- docs/brand/SOCIAL_AUTHORITY_V24.md
- docs/brand/MESSAGING_V1.md
- docs/brand/CLAIMS_POLICY_V1.md
- docs/brand/CHANNEL_MATRIX_V1.md

DevDay product evidence remains candidate/non-canonical in RUMBO-IA/rumbo-control-queue candidate/devday-* branches. Do not treat those branches as marketing publication authority.

## Authenticated social state
Upload-Post profile rumboia currently has 9 connected networks with no reauth requirement:
TikTok @rumboai; LinkedIn personal + RUMBO IA organization; YouTube @rumboagi; X @RumboAGI; Threads @rumbo.ia; Facebook personal; Instagram @rumbo.ia; Bluesky rumboia.bsky.social; Pinterest fedesebasc.

LinkedIn organization readback:
- RUMBO IA
- urn:li:organization:145014017
- followers: 2
- aggregate reach: 821
- aggregate impressions: 1266
- Sep 29 reach: 567
- page views: 13

Facebook Page readback: none found.

Current other distribution snapshots:
- X: 814 impressions on Sep 29
- Threads: 490 snapshot impressions, 331 on Sep 29, 1 like, 2 comments
- YouTube: 191 snapshot views; analytics marked stale by provider
- TikTok: 1 view
- Instagram: 0 current reach
- Pinterest: 0 current impressions

DISTRIBUTION_PROVEN != CONVERSION_PROVEN.

## Future Metricool state
Brand id 6769976. Timezone America/Buenos_Aires.
Campaign law: DRAFT_ONLY unless explicitly promoted later.

All future campaign items through Oct 9 are draft=true and autoPublish=false at this cut.

LinkedIn UUIDs:
- Sep 30 11:00 — 483958358470708143
- Oct 1 11:00 — 7427550803671469763
- Oct 2 11:00 — 3738731847919030059
- Oct 6 11:00 — -4267920369327586611
- Oct 7 11:00 — 2121282990394525723
- Oct 9 11:00 — 972309138653662832

Bluesky:
- Oct 1 11:00 — -3086047905255570494

On Sep 29 the Oct 2/6/7/9 LinkedIn items were corrected from draft=false/autoPublish=true to draft=true/autoPublish=false. UUID identity was preserved.

## Lead capture
DevDay priority form:
- Typeform T8Qi1DS4
- title: RUMBO IA — DevDay 2026 Leads
- response count: 0
- contract: priority/waitlist only
- not a download
- not automatic resource delivery

Commercial pilot intake:
- Typeform Tu3D3tVo
- response count: 1
- separate funnel; never attribute this response to DevDay

Typeform automation RUMBO IA — Inbound Intake Loop V1: DRAFT, trigger disabled, triggered=0.

## OpenAI claim gate
Primary sources:
- https://openai.com/index/devday-2026-recap/
- https://openai.com/index/introducing-dots/
- https://openai.com/index/introducing-the-agents-api/
- https://developers.openai.com/api/docs/guides/agents-api/overview
- https://developers.openai.com/api/docs/models/gpt-6.1-sol

Safe campaign facts at this cut:
- Dots are always-on agents with their own cloud computer/browser and plugin connections.
- Dots availability must be stated from the current primary page/recap, never inferred from account plan.
- GPT-6.1 Sol standard API pricing: $2 input / $0.10 cached input / $10 output per 1M tokens.
- The English DevDay recap states GPT-6.1 Sol is available to API and Plus/Pro/Business/Enterprise/Edu users and describes its standard input/output token pricing as one fifth of Astra.
- Agents API is public beta. OpenAI manages sessions/orchestration/context compaction/recovery; the application provides tools/workflow/environment.
- Agents API supports MCP, subagents and hosted/self-hosted environments.
- Agents API itself has no added platform fee; token/tool/container usage is billed normally.

Fail closed on localized-source inconsistencies. Do not publish a Sol Ultrafast availability claim until the current primary surfaces are reconciled.

## Public content debt
Published LinkedIn copy exceeded current evidence in several posts. Current connected tools provide readback but no safe edit/delete action for already-published LinkedIn content, so:
PUBLIC_CLEANUP_BLOCKED_BY_TOOLING.

Do not reuse or amplify unsupported claims from:
- https://www.linkedin.com/feed/update/urn:li:share:7510805694778929154
- https://www.linkedin.com/feed/update/urn:li:share:7510772378293927936
- https://www.linkedin.com/feed/update/urn:li:share:7510772072860606464
- https://www.linkedin.com/feed/update/urn:li:share:7510773368904630272
- https://www.linkedin.com/feed/update/urn:li:share:7510771297006567425
- https://www.linkedin.com/feed/update/urn:li:share:7510766501440958464
- https://www.linkedin.com/feed/update/urn:li:share:7510757159211655168
- https://www.linkedin.com/feed/update/urn:li:share:7510756641290715136

Problem classes include: claiming live Dots testing without runtime evidence; conflating $500 Pro 500 with Dots access; unverified Dots/Muse/Grok comparison; promising PDF/repo/calculator/live delivery not proven; “Dots SDK/commands” framing; excessive post-volume claims.

Correction strategy: no correction spam burst. One later evidence-first clarification may supersede the bad framing after explicit draft promotion.

## Editorial law
Positioning: RUMBO IA — evidence before hype.

ONE_STRONG_IDEA > MANY_NEAR_DUPLICATE_POSTS.

Pillars:
1. OpenAI launch -> exact availability/evidence boundary.
2. Agent reliability -> authority/state/readback/recovery/receipts.
3. Builder implementation -> real docs/API/code only.
4. Commercial application -> bounded human-controlled pilot.
5. Build in public -> failures/corrections explicitly labeled.

LinkedIn flagship window: around 11:00 ART where current Metricool best-time signal is strongest.
X/Threads/Bluesky: adapted summaries, not copy spam.
YouTube/TikTok/Instagram: native video/visual evidence, not recycled text.

## KPI ladder
IMPRESSION -> ENGAGED_VIEW -> PROFILE_VISIT -> CLICK -> FORM_RESPONSE -> QUALIFIED_CONVERSATION -> OPPORTUNITY -> CASH.

Current bottleneck:
DISTRIBUTION=PROVEN
DEVDAY_FORM_RESPONSES=0
QUALIFIED_DEVDAY_CONVERSION=NOT_PROVEN

## Scheduler
Existing task 6ab2debb62ec819194d47cd4c2cd7a37 is titled RUMBO Marketing + DevDay and remains DISABLED.
Its contract is campaign-only, zero-spend, fail-closed, no unrelated CI/Windows/GovOps drift, no duplicate watcher, and no autopublication.
DISABLED_SCHEDULE != FUTURE_EXECUTION.

## Next gate
1. Keep future posts draft-only.
2. Review one flagship post around Dots != Agents API and exact entitlement/API boundaries.
3. CTA T8Qi1DS4 remains waitlist/priority, never “download now”.
4. Build visual/video derivatives only from verified demos.
5. Measure conversion after one strong post before increasing frequency.
6. Reconcile the public-content debt only if a supported edit/delete surface appears.

CAMPAIGN_READY_FOR_REVIEW=true
CAMPAIGN_READY_FOR_AUTOPUBLISH=false
NEW_EXTERNAL_SPEND_USD=0
