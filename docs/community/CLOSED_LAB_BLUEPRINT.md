# RUMBO Closed Lab blueprint

Purpose: define the exact private collaboration surface to create when repository-administration authority is available.

## Repository

Recommended name: `RUMBO-IA/rumbo-closed-lab`.

Required posture:
- private;
- owner-only at creation;
- no production secrets;
- no customer data;
- no direct deployment;
- no organization-wide secrets;
- no self-hosted runner execution for untrusted code;
- GitHub Actions disabled initially unless a reviewed workflow requires it;
- synthetic or explicitly approved fixtures only.

## Access

Add people only when a real collaborator exists. Prefer repository-scoped outside-collaborator access over organization membership when one repository is sufficient.

Minimum role by default:
- Read for inspection;
- Triage for issue/PR organization;
- Write only when source changes are required;
- Maintain/Admin only by explicit owner decision.

## Promotion

Closed Lab output never moves directly to production. Promotion path:

`Closed Lab change -> review -> new integration branch in canonical repo -> canonical CI -> maintainer decision -> governed merge -> separate production authorization`

## Offboarding

On removal, verify repository membership, deploy keys, tokens, SSH keys, Codespaces, Actions secrets, app grants and AI-tool credentials. Record readback evidence.
