# RUMBO IA Content Canon V2

Status: CANDIDATE — content approval, publication authority and production deployment remain separate gates.

## Purpose
Turn RUMBO content into an evidence-backed system instead of a collection of copy drafts.
This canon is subordinate to BRAND_SYSTEM_V1, CLAIMS_POLICY_V1, MESSAGING_V1,
the identity registry and the channel/distribution locks.

## Authority order
1. Technical/commercial state and evidence receipts.
2. `identity_registry_v1.json` for identity admission.
3. `CLAIMS_POLICY_V1.md` for claim strength.
4. `MESSAGING_V1.md` for approved promise, offer and CTA vocabulary.
5. `content_registry_v2.json` for content-item state.
6. `distribution_lock_v1.json` for current cross-channel authority/readback.

Narrative social/readback documents are historical evidence when they conflict with the fresher machine-readable distribution lock.

A content draft never upgrades the product, customer, metric or deployment state.

## Lanes
- `RUMBO_BRAND`: company/product content under public expression `RUMBO IA`.
- `PERSONAL_BRAND`: founder/personal content; it may reference RUMBO evidence but does not inherit company identity automatically.

Cross-lane identity promotion is fail-closed.
Founder identity and RUMBO IA remain separate public surfaces unless a reviewed canon change explicitly authorizes otherwise.

## Publication states
- `SOURCE_MATERIAL`: recovered or historical material; not publishable as-is.
- `QUARANTINED`: unsupported, stale, identity-invalid or privacy-sensitive material.
- `CANDIDATE_SAFE`: reconciled to current policy but not publication-approved.
- `READY_FOR_HUMAN_REVIEW`: evidence and channel requirements are satisfied; human review still required.
- `PUBLISHED`: requires a publication receipt and authenticated readback.

`CANDIDATE_SAFE != READY_FOR_HUMAN_REVIEW != PUBLISHED`.

## Historical kits
Recovered Week 1 and Week 2 HTML kits are source material only.
Their former “ready to publish” labels have no publication authority.
Unsupported customer outcomes, percentages, fabricated case studies, legacy domains/offers,
unsupported algorithm/timing assertions and unknown identity tokens must not enter canonical content.

`NEXO` / `NEXO 3.0` are not admitted identities in the current identity registry and remain `SAFE_STOP` as RUMBO identity tokens.

## Current public positioning
Primary promise: **IA con control humano para organizar y automatizar operaciones comerciales.**

Commercial entry: **Revenue Recovery Sprint** — one bounded commercial workflow,
14 calendar days, USD 149 one-time before kickoff. Scope and baseline precede outcome claims.
Sensitive actions remain human-supervised. No ROI guarantee.

Canonical public domain: `https://rumbo.verso.fans`.

## Canonical Week 1
### W1-01 — Brand introduction
Lane: `RUMBO_BRAND` · Claim: `BUILT` · State: `CANDIDATE_SAFE`

La IA no debería quitarte el control de tu negocio. Debería ayudarte a ordenar mejor lo que ya pasa todos los días.
RUMBO IA construye sistemas de CRM y automatización con IA para pequeñas empresas.
El producto está construido y los pilotos controlados están en preparación.
Construimos. Probamos. Auditamos.
### W1-02 — Process-first education
Lane: `RUMBO_BRAND` · Claim: `BUILT` · State: `CANDIDATE_SAFE`

Cinco procesos para revisar antes de sumar más trabajo manual: preguntas repetitivas,
registro de consultas, seguimientos pendientes, clasificación inicial de oportunidades
y consulta de información interna aprobada.
Primero entender el proceso, después automatizarlo y recién entonces medir si mejoró.

### W1-03 — Commercial entry
Lane: `RUMBO_BRAND` · Claim: `BUILT` · State: `CANDIDATE_SAFE`

El Revenue Recovery Sprint toma un único flujo comercial durante 14 días.
Se define alcance y línea base, se automatiza solo el circuito acordado,
se mantiene supervisión humana y se mide antes de afirmar resultados.
Precio actual: USD 149, pago único antes del inicio. No se garantiza ROI.

## Week 2 reconciliation
- Education about automation: preserve concept; rewrite to current claim vocabulary.
- Pricing-by-AI demo: only as visibly labeled `DEMO/EXAMPLE`.
- “20+ companies in LATAM”: `QUARANTINED` until exact evidence exists.
- Engagement poll: reusable without invented benchmark claims.
- Restaurant 80→3 case study: `QUARANTINED` until permission + measured evidence exist.
- 2025 personal-brand post: `STALE` and `WRONG_LANE` for RUMBO_BRAND.
- Newsletter +38% benchmark: `QUARANTINED` until source, population and observation window are recorded.

## EP001
Working title: **Construí un sistema para que ChatGPT y Codex no pierdan el contexto**.
Series: `RUMBO Labs`. State: `SPECIFIED_NOT_RENDERED`.
Rendering, upload and publication require separate receipts.

## Visual and channel boundary
New content uses canonical Brand System tokens; legacy kit styling remains historical only.
Current channel authority is read from `docs/brand/distribution_lock_v1.json`.
As observed 2026-09-12, website, YouTube, X and LinkedIn are PASS in that lock.
This proves channel/distribution authority only; it does not prove that any content item in this registry was published.
A publish-capable connection is not profile-edit authority; a draft is not publication authority.

## Invariants
- `TECHNICAL_PASS != CONTENT_PUBLICATION_AUTHORITY`.
- `CONTENT_COMPLETE != PUBLISHED`.
- `PUBLISHED_ONCE != AUTO_PUBLISH_AUTHORITY`.
- `MEASURED_CLAIM_REQUIRES_EVIDENCE_RECEIPT`.
- `PERSONAL_BRAND != RUMBO_BRAND`.
- `UNKNOWN_IDENTITY = SAFE_STOP`.
- `AUTO_PUBLISH = NO_GO` unless a future reviewed policy explicitly changes this invariant.
