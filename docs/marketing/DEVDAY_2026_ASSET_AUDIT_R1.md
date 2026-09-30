# RUMBO IA — DevDay Campaign Asset Audit R1

Observed: 2026-09-29
Status: FAIL-CLOSED ASSET RECONCILIATION

## Google Drive legacy assets

The following existing assets are preserved as historical drafts but are NOT approved for campaign publication:

### Dots cheat sheet PDFs
Drive IDs:
- 1NdObKChazZzP4AhOTwaRm8ri4tolaYFz
- 1zehF9FrEMFOm4Uhy6W2YMcYsj1XBIBra
- 1SiJAZp6DvUZylPGHr7asCJ2NZ_WhFvNZ

Reason: they present invented/unverified “12 commands” such as `LongTermMemory`, `agent.deploy`, `AgentMonitor`, and `agent.ship`, plus an unsupported Dots/Muse/Grok comparison.

Verdict: `NO_GO`.

### Live tutorial
Drive ID: 1ZrFWLql2obJ7jB-OWJOgSNx6Z6CyIoC0

Reason: titled “Build your first DOTS agent in 5 minutes” but uses non-official pseudocode and conflates Dots with Agents API. It also promises repo/PDF delivery not proven.

Verdict: `NO_GO`.

### Dots landing
Drive ID: 1HJ5Q43jm2DFrjtdR7L0jIx0bbrq5QlIr

Reason: promises PDF, pricing calculator and live invite. The truthful current funnel is Typeform T8Qi1DS4 as a priority/waitlist, not automatic delivery.

Verdict: `NO_GO`.

### Legacy distribution pack
Drive README ID: 1zJdl3ERiDP-npNRTk9KE6dr5qdQGNaaT

The pack says it contains six covers, one video and a Buffer CSV. Treat it as source material only; its copy/assets require current claim review before reuse.

## Replacement branch assets

Campaign branch now owns safe candidates:
- docs/marketing/assets/DEVDAY_BUILDER_BRIEF_R1.md
- docs/marketing/assets/AGENTS_API_TUTORIAL_R1.md
- docs/marketing/assets/devday-waitlist-r1.html

These candidates:
- distinguish Dots from Agents API;
- use the official Agents API `beta.agents.sessions.create` surface;
- explicitly state that API execution may incur charges and was not run under zero-spend;
- use Typeform only as waitlist/prioritization;
- make no automatic-delivery claim.

## YouTube research surface

vidIQ MCP authentication:
- authenticated account: fscfede@gmail.com
- authorized YouTube channels returned: 0
- remaining credits: 4 / renewable plan cap 150
- analytics/research calls cost 5 credits each

Therefore no vidIQ paid-credit research was executed.

`VIDIQ_ACCOUNT_AUTHENTICATED=true`
`VIDIQ_YOUTUBE_CHANNEL_AUTHORIZED=false`
`VIDIQ_RESEARCH_SKIPPED_ZERO_SPEND=true`

## Release law

`ASSET_EXISTS != ASSET_APPROVED`
`PRIVATE_DRIVE_FILE != PUBLIC_DELIVERY`
`WAITLIST_SUBMISSION != RESOURCE_DELIVERED`
`DOCUMENTED_API_EXAMPLE != RUNTIME_EXECUTED`

NEW_EXTERNAL_SPEND_USD=0
