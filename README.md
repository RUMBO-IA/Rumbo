# RUMBO IA

[![Public privacy gate](https://github.com/RUMBO-IA/Rumbo/actions/workflows/privacy-gate.yml/badge.svg?branch=main)](https://github.com/RUMBO-IA/Rumbo/actions/workflows/privacy-gate.yml)

Human-controlled AI CRM and automation for small businesses in Latin America.

RUMBO IA helps small businesses organize customer conversations, leads, follow-ups, approved business knowledge and commercial workflows while keeping humans in control of sensitive decisions.

## Brand governance

RUMBO brand identity, naming roles, claim classes and publication guardrails are governed by [`docs/brand/BRAND_SYSTEM_V1.md`](docs/brand/BRAND_SYSTEM_V1.md) and the machine-readable [`docs/brand/identity_registry_v1.json`](docs/brand/identity_registry_v1.json). Generated or publishable identity names must pass the fail-closed brand admission contract; unknown or explicitly non-canonical names are not implicitly authorized.

## Engineering controls

The public repository keeps consequential behavior behind explicit verification boundaries:

- sensitive business actions remain human-supervised;
- the public privacy gate runs on branch pushes and on pull requests targeting `main`;
- CI checks public privacy invariants, commercial-offer coherence, security-header configuration, and the RUMBO brand contract on governed brand/public surfaces;
- repository security and reporting rules are documented in [`SECURITY.md`](SECURITY.md).

## Release posture

This repository distinguishes the mutable Git `main` branch from production traffic. The current `main` head is intentionally not hardcoded here; GitHub is the source of truth for the branch head. The production domain `rumbo.verso.fans` is intentionally serving the audited application commit `1aaf25d91d5fb1efd01f36fabd2f50e55f3d6c80` through Vercel deployment `dpl_Dua7MUambPmzntbFhDCFEmNoQodT`.

Changes to `main` do not automatically promote production: Git deployments for `main` are disabled, and production promotion is explicit and subject to the Safe Merge Authority gates.

## Current status

The core product is built and controlled commercial pilots are being prepared.

RUMBO IA is bootstrapped, founder-operated in Argentina and currently pre-revenue.

## Public links

- Website: https://rumbo.verso.fans
- AI Workflow Reliability Reference: https://sebastian-ai-workflow-reliability.miniup.app/

## Commercial entry

Revenue Recovery Sprint: one bounded commercial workflow, 14 calendar days, USD 149 one-time before kickoff. Scope is written before execution, a baseline is established before outcome claims, sensitive actions remain human-supervised, and no ROI is guaranteed. Any continuation is agreed separately.

Pilot intake: https://form.typeform.com/to/Tu3D3tVo

## Founder

Sebastián

Founder · Product & AI Systems Operator

## Contact

sebastian@rumbo.verso.fans
