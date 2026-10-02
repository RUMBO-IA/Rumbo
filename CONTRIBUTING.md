# Contributing to the public RUMBO repository

This repository is a public product and engineering surface for RUMBO IA. It is not the private production control plane.

## Suitable contributions

- fixes to the public website or documentation;
- tests and improvements for privacy, commercial-coherence, and security-header verification;
- accessibility, usability, and public developer-experience improvements;
- narrowly scoped fixes that preserve human supervision and the documented public boundaries.

## Do not include

- credentials, tokens, private keys, `.env` files, or client data;
- private RUMBO control-plane state, provider identifiers, or deployment secrets;
- changes that automate sensitive business actions without explicit human control;
- unverifiable ROI, production, security, or affiliation claims.

## Before opening a pull request

Run the public privacy regression tests, commercial-coherence tests, security-header verifier, and `git diff --check`. The protected `main` branch also requires the `privacy` and `Vercel` checks.

## Promotion identity

The privacy gate validates the exact HEAD commit identity and never grants a metadata bypass to GitHub-generated commits. Public changes must preserve the approved GitHub noreply author and committer identity. GitHub server-side rebase integration can create a new commit object and rewrite committer metadata after exact-head checks, so it is not an approved promotion path for privacy-sensitive changes. Validate the exact candidate SHA first, require the protected `privacy` and `Vercel` checks on that SHA, then promote only by a non-forced fast-forward of `main` to that same commit object. Re-read `main` immediately before promotion, stop if it moved or if the update is not a fast-forward, and verify the exact SHA plus the `privacy` push gate after promotion. Squash and merge-commit modes remain prohibited.

Undisclosed security issues belong in GitHub's private **Report a vulnerability** flow.