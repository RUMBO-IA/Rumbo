# RUMBO IA

[![Public privacy gate](https://github.com/RUMBO-IA/Rumbo/actions/workflows/privacy-gate.yml/badge.svg?branch=main)](https://github.com/RUMBO-IA/Rumbo/actions/workflows/privacy-gate.yml)

**Operational AI Systems** with human control, explicit boundaries and verifiable outcomes.

RUMBO IA builds operational AI systems across three public pillars: **Revenue Recovery**, **Agent Reliability**, and **Guardian**. Sensitive actions remain human-supervised, and public claims stay bounded to evidence that can be read back and verified.

## Brand governance

RUMBO brand identity, naming roles, claim classes and publication guardrails are governed by [`docs/brand/BRAND_SYSTEM_V1.md`](docs/brand/BRAND_SYSTEM_V1.md) and the machine-readable [`docs/brand/identity_registry_v1.json`](docs/brand/identity_registry_v1.json). Generated or publishable identity names must pass the fail-closed brand admission contract; unknown or explicitly non-canonical names are not implicitly authorized.

## Engineering controls

The public repository keeps consequential behavior behind explicit verification boundaries:

- sensitive business actions remain human-supervised;
- the public privacy gate runs on branch pushes and on pull requests targeting `main`;
- CI checks public privacy invariants, commercial-offer coherence, security-header configuration, and the RUMBO brand contract on governed brand/public surfaces;
- repository security and reporting rules are documented in [`SECURITY.md`](SECURITY.md).

## Community collaboration

RUMBO separates its public product/community front door from independently scoped open-source contributions:

- **[RUMBO Open Lab](https://github.com/RUMBO-IA/rumbo-open-lab)** — public, Apache-2.0-licensed experiments and community proposals. Start with its [contribution guide](https://github.com/RUMBO-IA/rumbo-open-lab/blob/main/CONTRIBUTING.md), [DCO 1.1 sign-off rules](https://github.com/RUMBO-IA/rumbo-open-lab/blob/main/DCO.md), and [security policy](https://github.com/RUMBO-IA/rumbo-open-lab/blob/main/SECURITY.md). Contributions use forks and pull requests; organization membership is not required.
- **[RUMBO community Discussions](https://github.com/RUMBO-IA/Rumbo/discussions)** — ideas and questions about the public product. Use [Issues](https://github.com/RUMBO-IA/Rumbo/issues/new/choose) for reproducible public problems; never include confidential details or credentials.
- **Private collaboration** — separate, explicitly approved, repository-scoped onboarding only. Public participation does not grant access to private labs, Core repositories, production systems, secrets, deployment authority, or paid resources.

The Open Lab license applies **only** within its stated repository scope; it does not license this product repository wholesale. A proposal, review or Open Lab merge does not authorize integration into production or proprietary Core. External contributions must satisfy their own rights, security and review gates before acceptance.

## Release posture

This repository distinguishes the mutable Git `main` branch from production traffic. The current `main` head is intentionally not hardcoded here; GitHub is the source of truth for the branch head. The owner-authorized production binding for `rumbo.verso.fans` is application commit `6eeadb84b1dd57f17c4a46891770d2425e83c742` through Vercel deployment `dpl_961FH2Y7gDi6T2unCTvii6AASvnb`, as authorized by canonical registry issue #72 comment `6001040749`. Live provider effect remains subject to exact promotion and readback.

Changes to `main` do not automatically promote production: Git deployments for `main` are disabled, and production promotion is explicit and subject to the Safe Merge Authority gates.

## Current status

The core product is built and controlled commercial pilots are being prepared.

RUMBO IA is bootstrapped, founder-operated in Argentina and currently pre-revenue.

## Public links

- Website: https://rumbo.verso.fans
- Trust Center: https://rumbo.verso.fans/trust-center
- AI Workflow Reliability Reference: https://sebastian-ai-workflow-reliability.miniup.app/

## Commercial entry

Revenue Recovery Sprint: one bounded commercial workflow, 14 calendar days, USD 149 one-time before kickoff. Scope is written before execution, a baseline is established before outcome claims, sensitive actions remain human-supervised, and no ROI is guaranteed. Any continuation is agreed separately.

Pilot intake: https://form.typeform.com/to/Tu3D3tVo

## Founder

Sebastián

Founder · Product & AI Systems Operator

## Contact

sebastian@rumbo.verso.fans
