# Contributing to the public RUMBO repository

This repository is RUMBO's public product and engineering surface. It is not the private production control plane.

## Choose the correct collaboration lane

### Public Open Lab

Use this repository for public code, documentation, tests, reproducible examples, synthetic fixtures, accessibility/usability work, and other changes that are safe to review in public.

Public contributors normally work through:

`Issue or proposal -> personal fork -> contributor branch -> pull request -> CI -> maintainer review`

A GitHub organization membership is not required.

Focused pull requests are welcome on this public surface. Search existing Issues and pull requests first and keep each change narrow enough to review.

### Private Closed Lab

Work that requires non-public collaboration belongs in a dedicated private lab repository after an explicit invitation. Closed Lab access never grants access to canonical control, runtime, production, customer data, or production credentials.

### Canonical/Core repositories

Sensitive canonical repositories use a stricter collaborator-only model. An external contributor should not prepare changes for those repositories unless a maintainer explicitly opens that path.

## Suitable public contributions

- fixes to the public website or documentation;
- tests and improvements for privacy, commercial-coherence, and security-header verification;
- accessibility and usability improvements;
- focused public engineering utilities;
- examples or synthetic fixtures that do not expose private state;
- narrowly scoped fixes that preserve human supervision and documented boundaries.

## Do not include

- credentials, tokens, private keys, `.env` files, or client data;
- private RUMBO control-plane state, provider identifiers, or deployment secrets;
- production access instructions;
- changes that automate sensitive business actions without explicit human control;
- unverifiable ROI, production, security, or affiliation claims.

## Before opening a pull request

Run the public privacy regression tests, commercial-coherence tests, security-header verifier, and `git diff --check`.

Explain:
- the problem;
- the smallest proposed change;
- how you tested it;
- whether the change needs any external service, credential, paid resource, or network access.

Any external cost must be clearly opt-in. The default contribution path must remain usable without RUMBO-funded compute.

## Contribution does not imply authority

`CONTRIBUTED != REVIEWED != ACCEPTED != MERGED != DEPLOYED != PRODUCTION_AUTHORIZED != LIVE_EFFECT_VERIFIED`

A green check does not grant merge or production authority.

## Promotion identity

The privacy gate validates exact commit identity and does not grant metadata exceptions to generated commits.

Public changes must preserve an approved public Git author and committer identity. Validate the exact candidate SHA, require the protected checks on that SHA, and use the governed promotion procedure.

## Security

Undisclosed security issues belong in GitHub's private **Report a vulnerability** flow described in `SECURITY.md`. Do not publish vulnerability details in Issues, pull requests, Discussions, or community chat.

## Want to collaborate more deeply?

Use the **Collaboration proposal** Issue form. Repeated useful contributions may lead to additional repository-scoped responsibilities, but no role upgrade is automatic.

## Interim external-contribution acceptance gate

Public pull requests from third parties may be opened and reviewed while RUMBO finalizes the Open Lab licensing and inbound-contribution policy.

Until this public repository publishes an explicit outbound license and an approved inbound-contribution policy:

- maintainers may discuss, review, test, and request changes to an external contribution;
- externally authored code or documentation is not authorized for merge as an accepted Open Lab contribution;
- no public pull request creates employment, partnership, repository authority, or a license grant by implication;
- do not submit material whose ownership or submission rights are uncertain.

When the policy is activated, this section must be replaced or updated together with the published license and contributor terms.

## Repository boundary

This repository is the current public product/community front door; it is not automatically the licensed Open Lab codebase.

The target structure uses a dedicated public `RUMBO-IA/rumbo-open-lab` repository for code that RUMBO explicitly chooses to publish under an open-source license. Until that repository and its license/inbound terms exist, public pull requests here remain evaluation proposals under the interim acceptance gate above.

A license selected for the future Open Lab must not be assumed to apply to private Core repositories or to unrelated public RUMBO source.
