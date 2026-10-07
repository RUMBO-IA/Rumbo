# Contributing to the public RUMBO repository

This repository is RUMBO's public product and engineering surface. It is not the private production control plane.

## Choose the correct collaboration lane

### Public product/community front door — this repository

`RUMBO-IA/Rumbo` is the public product and community front door. For people who are not repository collaborators, the default contribution path here is:

`bug / idea / analysis -> Issue or Collaboration proposal -> maintainer triage`

External code pull requests to this repository are not an accepted integration path. If one is opened, maintainers may inspect it as evidence or a prototype, then close or redirect it. It does not become mergeable merely because CI runs.

Repository collaborators may use pull requests for governed product changes under the existing authority controls.

### Public Open Lab — dedicated repository

Community code contributions belong in the future `RUMBO-IA/rumbo-open-lab` repository after it is provisioned with an explicit outbound license and approved inbound-contribution terms.

The Open Lab contribution path will be:

`Issue or proposal -> personal fork of rumbo-open-lab -> contributor branch -> secretless untrusted CI -> maintainer review -> internal acceptance candidate`

A GitHub organization membership is not required for the public fork path.

### Private Closed Lab

Work that requires non-public collaboration belongs in a dedicated private lab repository after an explicit invitation. Closed Lab access never grants access to canonical control, runtime, production, customer data, or production credentials.

### Canonical/Core repositories

Sensitive canonical repositories use a stricter collaborator-only model. An external contributor should not prepare changes for those repositories unless a maintainer explicitly opens that path.

## Suitable public input on this repository

- reproducible bug reports and sanitized diagnostics;
- root-cause analysis and technical observations;
- accessibility and usability feedback;
- focused design proposals;
- public-safe documentation corrections proposed through an Issue;
- ideas for examples, tests, tools, or synthetic fixtures that may later belong in the Open Lab.

Maintainers may implement an accepted idea directly in this repository or move an explicitly publishable work item into the dedicated Open Lab once that repository is active.

## Do not include

- credentials, tokens, private keys, `.env` files, or client data;
- private RUMBO control-plane state, provider identifiers, or deployment secrets;
- production access instructions;
- changes that automate sensitive business actions without explicit human control;
- unverifiable ROI, production, security, or affiliation claims.

## Before opening a pull request

If you are not a repository collaborator, open an Issue or Collaboration proposal instead of preparing an integration PR against `RUMBO-IA/Rumbo`.

Repository collaborators opening governed product PRs must run the public privacy regression tests, commercial-coherence tests, security-header verifier, and `git diff --check`.

Explain:
- the problem;
- the smallest proposed change;
- how you tested it;
- whether the change needs any external service, credential, paid resource, or network access.

Any external cost must be clearly opt-in. The default community path must remain usable without RUMBO-funded compute.

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

GitHub may technically allow a third party to open a pull request against this public repository. Such a pull request is evaluation-only and may be closed or redirected to an Issue.

Until the dedicated Open Lab publishes an explicit outbound license and approved inbound-contribution policy:

- maintainers may inspect an external patch as evidence or a prototype;
- externally authored code or documentation is not authorized for merge as an accepted community contribution;
- no public pull request creates employment, partnership, repository authority, or a license grant by implication;
- do not submit material whose ownership or submission rights are uncertain.

When the policy is activated, this section must be replaced or updated together with the published license and contributor terms.

## Repository boundary

This repository is the current public product/community front door; it is not automatically the licensed Open Lab codebase.

The target structure uses a dedicated public `RUMBO-IA/rumbo-open-lab` repository for code that RUMBO explicitly chooses to publish under an open-source license. Until that repository and its license/inbound terms exist, public pull requests here remain evaluation proposals under the interim acceptance gate above.

A license selected for the future Open Lab must not be assumed to apply to private Core repositories or to unrelated public RUMBO source.
