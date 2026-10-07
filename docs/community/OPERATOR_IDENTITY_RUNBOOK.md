# RUMBO operator identity runbook

Purpose: prevent account, credential, browser, Git, and AI-tool context from being mistaken for one another.

## Invariant

`BROWSER_PROFILE != GITHUB_ACCOUNT != GH_CLI_AUTH != GIT_AUTHOR != SSH_KEY != OPENAI_ACCOUNT != CODEX_STATE != REPOSITORY_ROLE != AUTHORITY`

## Before any Git write

Record or verify all of the following for the current checkout:

1. repository owner/name;
2. current branch and upstream;
3. active GitHub CLI identity;
4. Git author name and email configured for this repository;
5. remote URL and authentication method;
6. SSH key or credential path selected for this repository;
7. browser profile used for any web-only approval;
8. AI-tool account/state used for assistance;
9. maximum authority allowed for this checkout.

If any item is ambiguous, stop before pushing.

## GitHub CLI

Check the active accounts with:

`gh auth status`

When more than one GitHub account is actually authenticated, switch explicitly:

`gh auth switch --hostname github.com --user <login>`

Do not infer CLI identity from the account visible in a browser.

## Git author

Prefer repository-local Git identity rather than relying on a global identity:

`git config user.name "<approved-name>"`

`git config user.email "<approved-email>"`

Verify before committing:

`git config --get user.name`

`git config --get user.email`

## Multiple SSH identities

If multiple GitHub user accounts are used from one workstation, give each account a distinct SSH key and host alias with `IdentitiesOnly yes`, or use a repository-specific `GIT_SSH_COMMAND`.

Never share a private SSH key between people.

## HTTPS identities

For HTTPS with multiple GitHub accounts, keep credentials repository-specific. GitHub documents `credential.https://github.com.useHttpPath true` as a way to keep credentials separated by repository path.

## Browser profiles

A browser profile is only a session container. It does not grant Git, repository, OpenAI, Codex, deployment, or production authority.

Keep personal and RUMBO browser contexts separate and name them clearly.

## AI coding contexts

Keep AI coding state separate from GitHub authority. Different OpenAI/Codex accounts or separate `CODEX_HOME` roots may isolate AI history and credentials, but they do not create distinct GitHub reviewers.

## Three-role operator model

RUMBO may use these logical roles even when one human temporarily operates all three:

- **A — Owner / Recovery:** account recovery and administrative continuity.
- **B — Builder:** normal development work.
- **C — Automation / Test:** bounded automation and non-human verification.

A, B, and C count as distinct GitHub actors only after separate GitHub identities are actually established and their permissions are separately verified.

## Pre-push proof

A safe push should be explainable as:

`checkout -> active GitHub identity -> Git author -> credential -> repository role -> intended branch -> allowed action`

If that chain cannot be stated unambiguously, do not push.
