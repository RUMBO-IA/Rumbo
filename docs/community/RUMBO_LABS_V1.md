# RUMBO Labs V1 — collaboration and sandbox model

Status: candidate policy for public review. This document does not grant access by itself.

## 1. Goal

RUMBO uses two collaboration areas:

1. **RUMBO Open Lab** — public, fork-first, community-friendly.
2. **RUMBO Closed Lab** — private, invitation-only, isolated from canonical production/control repositories.

The design keeps identity, repository access, compute, secrets, source integration, deployment, and production authority as separate capabilities.

## 2. Identity rule

Every human uses their own GitHub identity. Credentials are never shared.

Owner-controlled accounts must each have a declared purpose and must not be treated as interchangeable identities. The operating invariant is:

`PROFILE != ACCOUNT != AUTHORITY`

A browser profile, GitHub account, OpenAI/Codex account, API identity, and production authority are different objects even when operated by the same person.

## 3. Open Lab

Target public repository: `RUMBO-IA/rumbo-open-lab`.

It is not yet provisioned. Until it exists with approved license and inbound terms, `RUMBO-IA/Rumbo` acts as the public product/community front door and external contributors should use Issues and collaboration proposals rather than product-code integration PRs.

Once activated, the Open Lab contribution path is:

`idea/bug -> issue -> contributor fork of rumbo-open-lab -> contributor branch -> secretless untrusted CI -> maintainer review -> internal acceptance candidate`

Community contributors do **not** need organization membership or direct upstream write access. Public forks are the default source sandbox.

Open Lab may accept explicitly publishable code, examples, tests, documentation, synthetic fixtures, defensive research, and tooling.

Never place private control-plane state, customer data, credentials, production secrets, private provider identifiers, or non-public business records in this lane.

## 4. Closed Lab

Create a dedicated private repository for bounded external collaboration. Do **not** repurpose `rumbo-control-queue` or `rumbo-product-runtime` as the contributor sandbox.

Closed Lab requirements:

- invitation-only;
- synthetic or explicitly approved data only;
- no production credentials;
- no organization-wide secrets;
- no deploy keys shared between people;
- no direct production deployment;
- no self-hosted RUMBO runners for untrusted contributor code;
- default `GITHUB_TOKEN` read-only unless a specific workflow proves a narrower write need;
- external apps require owner approval;
- contributor access is limited to the lab repository, not the whole organization;
- removal of a contributor triggers access review and credential/session invalidation where applicable.

A Closed Lab result reaches a canonical private repository only by a new, reviewed integration change. Lab access is never equivalent to canonical write authority.

## 5. Repository roles

Use the minimum role that satisfies the task:

| Persona | Default access |
| --- | --- |
| Public contributor | Issues/proposals on Rumbo; fork + PR on Open Lab once active |
| Community triager | Triage on public repo only |
| Trusted public maintainer | Write only where needed |
| Private lab contributor | Write on Closed Lab only |
| Private lab reviewer | Triage/Write only on Closed Lab |
| Canonical maintainer | Separate explicit access to canonical repo |
| Organization owner | Extremely limited; never granted for contribution convenience |

Outside collaborators should be preferred over full organization membership when a person only needs one bounded private repository, subject to current plan/license constraints.

## 6. Sandbox model

### Public

Preferred zero-new-spend sequence:

1. Contributor discusses the work through `RUMBO-IA/Rumbo` Issues or the Open Lab issue tracker.
2. Once the dedicated Open Lab is active, the contributor forks `RUMBO-IA/rumbo-open-lab`.
3. Contributor opens the fork in their own local dev container or personal GitHub Codespaces quota.
4. The environment receives no RUMBO production secrets.
5. The contributor opens a PR against the Open Lab upstream.
6. Fork PR workflows are treated as untrusted, receive no repository/organization secrets, and run only on GitHub-hosted or contributor-owned isolated compute.

### Private

A private contributor sandbox is a dedicated private repository and/or ephemeral Codespace created from that repository. The lab must not request cross-repository write permissions in `devcontainer.json`.

If Codespaces usage would charge RUMBO, the action is fail-closed under the USD 0 external-spend policy. Personal included quota or local Dev Containers are preferred.

## 7. CI trust boundary

Untrusted contributor code must not execute with organization/repository secrets.

Use `pull_request` for untrusted fork testing. Avoid any workflow pattern that checks out and executes fork code under a privileged `pull_request_target`, `issue_comment`, or `workflow_run` context.

RUMBO self-hosted runners are reserved for trusted, reviewed code paths. Public community PRs do not run on them.

## 8. Promotion states

These states are deliberately separate:

`CONTRIBUTED != REVIEWED != ACCEPTED != MERGED != DEPLOYED != PRODUCTION_AUTHORIZED != LIVE_EFFECT_VERIFIED`

A contribution can stop at any state.

## 9. Community surfaces

GitHub is the authority for source collaboration. A Discord or other chat community may be used for discussion and onboarding, but it does not grant repository access or production authority.

Recommended public intake:

- GitHub Issues for bugs and scoped ideas;
- Pull Requests for governed collaborator changes in `RUMBO-IA/Rumbo`, and for public community code in the dedicated Open Lab once activated;
- GitHub Discussions for Q&A, proposals, showcases, and community coordination when enabled;
- private vulnerability reporting for undisclosed security issues.

## 10. Account model for RUMBO's own operators

RUMBO's owner-controlled GitHub accounts should be normalized into an identity registry with, at minimum:

- account login;
- owner/person;
- purpose;
- allowed organizations/repositories;
- browser/profile binding;
- authentication method;
- whether it may approve reviews;
- whether it may deploy;
- whether it may access secrets;
- recovery path.

No account should gain authority merely because it is logged into the same computer or browser.

## 11. Onboarding contract

Before a third party gets private access, record:

- GitHub username;
- collaboration scope;
- repository;
- role;
- start date;
- expected end/review date;
- IP/license terms;
- confidentiality requirement, if any;
- whether AI coding tools are allowed;
- data classes allowed in prompts;
- explicit prohibited systems;
- access revocation owner.

Public contributors need no private-access record unless they are promoted to a trusted role.

## 12. Zero-spend rule

This model must operate with no new paid service by default.

Public collaboration can work entirely through Issues and Discussions on the front door plus, once activated, Open Lab forks and pull requests, local Dev Containers, and contributors' own included resources.

Any private-seat, Codespaces, Actions, cloud sandbox, storage, AI, or marketplace action that may create new spend remains blocked until cost is proven to be USD 0 or separately authorized.

## 13. Physical repository boundary

The collaboration model should be implemented as separate repositories, not only as labels inside one codebase:

- `RUMBO-IA/Rumbo`: public product/community front door and bootstrap governance;
- `RUMBO-IA/rumbo-open-lab`: dedicated public, explicitly licensed Open Lab for community code;
- `RUMBO-IA/rumbo-closed-lab`: dedicated private collaboration/incubation repository;
- canonical private control/runtime repositories: separate Core authority.

This boundary limits license spillover and access spillover. Publishing or licensing Open Lab material does not publish, license, or authorize access to Core, Closed Lab, customer data, production credentials, or unrelated RUMBO source.

Until `rumbo-open-lab` is provisioned with approved license and inbound terms, `RUMBO-IA/Rumbo` accepts Issues and proposals as the external intake path. Third-party product-code pull requests are evaluation-only if opened and may be closed or redirected; they are not an accepted integration path.
