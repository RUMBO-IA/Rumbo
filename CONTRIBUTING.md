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

Undisclosed security issues belong in GitHub's private **Report a vulnerability** flow.