# RUMBO IA

[![Public privacy gate](https://github.com/RUMBO-IA/Rumbo/actions/workflows/privacy-gate.yml/badge.svg?branch=main)](https://github.com/RUMBO-IA/Rumbo/actions/workflows/privacy-gate.yml)

Human-controlled AI CRM and automation for small businesses in Latin America.

RUMBO IA helps small businesses organize customer conversations, leads, follow-ups, approved business knowledge and commercial workflows while keeping humans in control of sensitive decisions.

## Engineering controls

The public repository keeps consequential behavior behind explicit verification boundaries:

- sensitive business actions remain human-supervised;
- the public privacy gate runs on branch pushes and on pull requests targeting `main`;
- CI checks public privacy invariants, commercial-offer coherence, and security-header configuration;
- repository security and reporting rules are documented in [`SECURITY.md`](SECURITY.md).

## Release posture

This repository distinguishes the Git `main` state from production traffic. The authoritative code state is the `main` branch ref itself; this README deliberately does not pin a `main` SHA because the commit containing that value would make it stale. The production domain `rumbo.verso.fans` is intentionally serving the audited application commit `35af1ddc7a000069f686574f750f16bec2926dc4` through Vercel deployment `dpl_6NvixhNBiCbUUmSjnPJWC5MjB9ni`.

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

Founder · AI Systems & Agent Reliability Engineer

## Contact

sebastian@rumbo.verso.fans
