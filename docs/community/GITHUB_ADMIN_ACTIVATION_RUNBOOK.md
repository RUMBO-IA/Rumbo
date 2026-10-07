# GitHub administrative activation runbook

This runbook covers settings that cannot currently be changed through the connected GitHub integration.

## 1. Create Closed Lab

Create a new private repository named `rumbo-closed-lab` under `RUMBO-IA`.
Do not initialize it with secrets or production configuration.
Initial access: organization owners only.

## 2. Enable Discussions on the public RUMBO repository

Repository Settings -> General/Features -> Discussions -> enable.

Recommended categories:
- Announcements;
- Q&A;
- Ideas;
- Show and tell.

Source-of-truth remains Issues and Pull Requests for actionable engineering work.

## 3. Organization community-health defaults

In the public `RUMBO-IA/.github` repository, add organization defaults for:
- CONTRIBUTING.md
- CODE_OF_CONDUCT.md
- SECURITY.md
- SUPPORT.md
- issue templates
- pull-request template

Repository-local files continue to override organization defaults.

## 4. Ruleset refinement

Preserve privacy/identity controls globally.
Review the current non-fast-forward rule and scope it to canonical/release branches if temporary branches need normal cleanup.
Do not weaken required checks on `main`.

## 5. Verification

After each administrative mutation:
- read the setting back from GitHub;
- capture exact repository and branch;
- record actor and timestamp;
- confirm no billing-enabled feature was activated;
- record the receipt in the canonical control-plane issue.
