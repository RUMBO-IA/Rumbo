# RUMBO public collaboration governance

This file defines authority boundaries for the public RUMBO repository. It does not grant repository access.

## Roles

- **Public contributor:** works through a fork and pull request; no upstream write access is required.
- **Community triager:** may organize Issues and pull requests without source-write authority.
- **Maintainer:** reviews and integrates changes within the repository scope.
- **Private-lab collaborator:** works only in a dedicated private lab repository when explicitly invited.
- **Canonical maintainer:** has separate authority over private canonical repositories.
- **Organization owner:** retains administrative authority and is not a normal contributor role.

Minimum privilege is the default. A person receives only the repository role needed for the task.

## Authority states

These states are independent:

`CONTRIBUTED != REVIEWED != ACCEPTED != MERGED != DEPLOYED != PRODUCTION_AUTHORIZED != LIVE_EFFECT_VERIFIED`

Passing CI does not grant merge or production authority.

## Open Lab

Public collaboration is fork-first. Contributors use their own GitHub identity, their own workstation or personal sandbox resources, and public or synthetic data only.

Untrusted pull-request code receives no RUMBO production credentials and does not execute on RUMBO self-hosted runners.

## Closed Lab

Private external collaboration belongs in a dedicated private repository, not in canonical control or runtime repositories.

Closed Lab access is invitation-only, repository-scoped, revocable, and separated from production. Results move into canonical repositories only through a new reviewed integration change.

## Reviews and conflicts

A contributor must not be treated as an independent reviewer of their own work merely because the same person operates another browser profile, AI account, automation context, or machine identity.

## Cost boundary

No collaboration feature may create new external spend unless the cost is independently verified as zero or separately authorized.
