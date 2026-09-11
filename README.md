# RUMBO

[![Public privacy gate](https://github.com/RUMBO-IA/Rumbo/actions/workflows/privacy-gate.yml/badge.svg?branch=main)](https://github.com/RUMBO-IA/Rumbo/actions/workflows/privacy-gate.yml)

**Verified Agent Systems**

**Intelligence into Action.**

RUMBO builds reliable AI systems that move from intent to controlled, verifiable execution.

We focus on the infrastructure around intelligent agents: bounded authority, controlled execution, readback, evidence, verification and recovery.

`INTENT → AUTHORITY → PREFLIGHT → EXECUTION → READBACK → EVIDENCE → VERIFICATION`

## What we build

- **Agents** — systems designed to perform useful work across tools and environments.
- **Reliability** — control planes, gates, recovery mechanisms and operational safeguards.
- **Evidence** — receipts, attestations and verification systems that distinguish claims from demonstrated outcomes.
- **Applied systems** — human-controlled CRM and automation workflows for small businesses in Latin America.

## Engineering controls

The public repository keeps consequential behavior behind explicit verification boundaries:

- sensitive business actions remain human-supervised;
- the public privacy gate runs on branch pushes and pull requests targeting `main`;
- CI checks public privacy invariants, commercial-offer coherence, and security-header configuration;
- repository security and reporting rules are documented in [`SECURITY.md`](SECURITY.md).

## Release posture

This repository distinguishes the mutable Git `main` branch from production traffic. GitHub is the source of truth for the current branch head.

The production domain `rumbo.verso.fans` is intentionally serving the audited application commit `35af1ddc7a000069f686574f750f16bec2926dc4` through Vercel deployment `dpl_6NvixhNBiCbUUmSjnPJWC5MjB9ni`.

Changes to `main` do not automatically promote production: Git deployments for `main` are disabled, and production promotion is explicit and subject to the Safe Merge Authority gates.

## Current status

The core product is built and controlled commercial pilots are being prepared.

RUMBO is bootstrapped, founder-operated in Argentina and currently pre-revenue.

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

---

**RUMBO** · Verified Agent Systems · *Intelligence into Action.*
