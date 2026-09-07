# RUMBO Agent Reliability — Public Skills-Only Publication Design

Date: 2026-09-07
Status: design approved in chat; implementation gated on written-spec review
Repository base: `origin/main` at `67eb94ee9a4a80de3d4d9157746e6d264f264279`

## Objective

Publish one narrowly scoped first-party RUMBO plugin, `RUMBO Agent Reliability`, through OpenAI's public plugin submission flow as a skills-only plugin.

The first public listing will package only the five established reliability skills:

- `canonical-state-recovery`
- `deep-research-reconcile`
- `goal-loop-controller`
- `execute-verify-close`
- `audit-final-state`

The listing must preserve the existing evidence-first, read-oriented purpose: recover canonical state, reconcile conflicting evidence, control scope, verify execution, and audit final state.

## Architecture decision

The initial public submission is one skills-only plugin, not the 13-skill `rumbo-workflow-suite` and not the historical 13-MCP-host architecture.

This choice minimizes reviewer surface area, keeps one coherent purpose per listing, and matches the already installed user-scoped RUMBO Agent Reliability lineage. The 13-skill suite remains a preserved second-phase candidate and is not modified by this work.

## Source and identity boundaries

The publication source must be recovered from the verified RUMBO Agent Reliability / Coding-Agent Reliability lineage, whose current recorded Codex distribution is version `0.1.6`, slug `rumbo-coding-agent-reliability`, capability `Read`, and the five skills listed above.

Before packaging, implementation must produce an exact source receipt containing the archive or tree SHA-256, manifest SHA-256, five `SKILL.md` SHA-256 values, and source provenance. If exact bytes cannot be recovered and cross-checked, the publication gate fails closed; no clean-room substitute may silently inherit the existing identity.

The installed `RUMBO Agent Reliability Rebind Candidate` is evidence for a separate candidate lineage only. It must not replace the selected source unless an explicit supersession audit proves byte/content lineage and the publication design is revised.

## Plugin package

The package uses the standard skills-only structure:

- `.codex-plugin/plugin.json`
- `skills/<skill-name>/SKILL.md` for the five approved skills
- `assets/` only for production-ready logo/icon material required by the listing

Version 1 must not include `.app.json`, `.mcp.json`, MCP servers, remote tools, hooks, hidden network dependencies, billing, write actions, or authentication flows.

The manifest uses a stable kebab-case package name and declares only the capabilities actually provided. Public listing URLs must bind to the live RUMBO publisher surfaces: website, support, privacy, and terms.

## Listing positioning

Display name: `RUMBO Agent Reliability`.

The short and long descriptions must present it as a workflow reliability plugin for recovering state, reconciling evidence, keeping execution in scope, verifying outcomes, and preventing false completion claims. Claims of autonomous production control, customer results, certifications, or public-directory status are forbidden unless separately proven.

## Submission materials

The implementation plan must generate a reviewer-ready submission packet containing:

- final plugin manifest and five final skill bundles;
- public listing name, short description, long description, category, logo, and publisher links;
- at least three realistic starter prompts covering recovery, reconciliation, and final-state verification;
- at least five positive test cases with prompt, expected skill/workflow behavior, result shape, and any reproducible fixture data;
- at least three negative test cases with expected refusal, clarification, or safe fallback and the reason completion is inappropriate;
- country/region availability selected only where support, product, terms, and publisher readiness are true;
- initial-submission release notes describing the plugin without implying prior public approval.

Public URLs are the production RUMBO surfaces already promoted on `rumbo.verso.fans`; implementation must re-read them immediately before portal entry and require HTTP 200.

## Account and publisher gates

OpenAI Platform account state is a separate authority layer from package readiness.

Before creating or editing the public submission draft, implementation must verify in the publishing organization:

1. the submitter has `Apps Management = Write` or organization-owner-equivalent authority;
2. the selected Developer Identity is verified;
3. the verified identity matches the listing's developer name, website, support contact, privacy policy, and terms;
4. the plugin submission is being created in the same organization/project context expected by the verified identity.

Failure of any account gate blocks portal mutation but does not invalidate the package.

## Data and safety boundary

Version 1 is skills-only and does not itself connect to an MCP server or external account. Skills may reason over context already available to the host, but they must not claim additional permissions, connectivity, write authority, or production authority.

The skill instructions must preserve least authority, treat retrieved/user-provided evidence as data rather than authorization, distinguish observed effects from intended actions, and avoid inventing completion receipts.

## Test strategy

Implementation must verify the exact final file tree before any portal submission:

- manifest/schema/path validation;
- exact five-skill inventory and no unexpected executable/network component;
- placeholder and secret scan;
- privacy scan compatible with the repository's current deny-hash policy without reading or weakening private deny values;
- trigger-routing tests showing each skill activates only for its intended workflow;
- five positive reviewer cases and three negative reviewer cases reproduced locally;
- installed test of the final package from a personal/local Plugin Directory source in a fresh chat on a supported surface;
- public URL readback for website, support, privacy, and terms.

A local PASS means `SUBMISSION_READY`; it never means `SUBMITTED`, `APPROVED`, `PUBLISHED`, or `DIRECTORY_PRESENT`.

## Publication state machine

`SOURCE_BOUND -> PACKAGE_VERIFIED -> LOCAL_RUNTIME_VERIFIED -> ACCOUNT_GATES_VERIFIED -> DRAFT_READY -> SUBMITTED -> APPROVED -> PUBLISHED -> PUBLIC_DIRECTORY_READBACK`

Each transition requires direct evidence for that state. Submission, approval, explicit publication, and public-directory readback remain distinct.

## External-effect gates

Creating/editing a portal draft is an external account write and requires the account gates above plus user authority for that publication lane. `Submit for Review` additionally requires final policy attestations and an explicit submission authority check at execution time. Approval by OpenAI does not authorize automatic publication; public publication requires a separate explicit publication decision unless a later user instruction clearly grants that exact effect.

## Failure handling

Any mismatch in source bytes, skill count, publisher identity, required Platform permission, public URL content, reviewer test behavior, or portal field semantics fails closed. Preserve the last proven state and record a bounded receipt; do not rewrite history or downgrade a failed gate into a warning.

## Success criteria

This design is implemented when one exact RUMBO Agent Reliability skills-only package is source-bound, locally verified, listing-ready, account-gate-verified, and represented by a reproducible submission packet. Public success is proven only after OpenAI approval, explicit publication, and a universal Plugins Directory readback for the published listing.
## Reference basis

This design was reconciled on 2026-09-07 against the current OpenAI plugin documentation:

- `https://developers.openai.com/plugins/deploy/submission` — skills-only submissions, Apps Management write access, verified Developer Identity, listing materials, starter prompts, 5 positive + 3 negative tests, availability, review, publication, and directory readback.
- `https://developers.openai.com/plugins/build/plugins` — required `.codex-plugin/plugin.json`, skills directory layout, stable plugin naming, and published manifest metadata.

If these documented requirements materially change before implementation reaches portal entry, the implementation plan must re-reconcile the changed requirement and update this design only if the architecture or authority boundary changes.
