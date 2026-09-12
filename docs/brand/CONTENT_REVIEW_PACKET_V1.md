# RUMBO IA Content Review Packet V1

Status: REVIEW_PACKET ? non-authoritative aid for human review; it does not grant publication authority.

## Authority boundary
- Governing sources: `BRAND_SYSTEM_V1.md`, `CLAIMS_POLICY_V1.md`, `MESSAGING_V1.md`, `CHANNEL_MATRIX_V1.md`, and `content_registry_v2.json`.
- `READY_FOR_HUMAN_REVIEW != APPROVED != PUBLISHED`.
- `DISTRIBUTION=PASS != CONTENT_PUBLISHED`.
- `AUTO_PUBLISH=NO_GO`.
- Automated/agent lanes do not issue approval receipts; approval requires explicit human input.

## Scope
The following five items satisfied the current machine gates for evidence, identity, copy presence, claim discipline and distribution readiness. Target review channels are LinkedIn and X only.

### W1-01
- Lane: `RUMBO_BRAND`
- Identity: `RUMBO IA`
- Claim class: `BUILT`
- Target channels: `LinkedIn`, `X`
- Evidence: `README.md`, `docs/brand/MESSAGING_V1.md`
- Copy: La IA no debería quitarte el control de tu negocio. RUMBO IA construye sistemas de CRM y automatización con IA para pequeñas empresas. El producto está construido y los pilotos controlados están en preparación. Construimos. Probamos. Auditamos.

### W1-02
- Lane: `RUMBO_BRAND`
- Identity: `RUMBO IA`
- Claim class: `BUILT`
- Target channels: `LinkedIn`, `X`
- Evidence: `docs/brand/MESSAGING_V1.md`
- Copy: Cinco procesos para revisar antes de sumar más trabajo manual: preguntas repetitivas, registro de consultas, seguimientos pendientes, clasificación inicial de oportunidades y consulta de información interna aprobada. Primero entender el proceso, después automatizarlo y recién entonces medir si mejoró.

### W1-03
- Lane: `RUMBO_BRAND`
- Identity: `RUMBO IA`
- Claim class: `BUILT`
- Target channels: `LinkedIn`, `X`
- Evidence: `README.md`, `docs/brand/MESSAGING_V1.md`
- Copy: El Revenue Recovery Sprint toma un único flujo comercial durante 14 días. Se define alcance y línea base, se automatiza solo el circuito acordado, se mantiene supervisión humana y se mide antes de afirmar resultados. Precio actual: USD 149, pago único antes del inicio. No se garantiza ROI.

### W2-01
- Lane: `RUMBO_BRAND`
- Identity: `RUMBO IA`
- Claim class: `BUILT`
- Target channels: `LinkedIn`, `X`
- Evidence: `docs/brand/MESSAGING_V1.md`
- Copy: Automatizar empieza por mapear un proceso concreto: entrada, decisión, acción, excepción y revisión humana. La herramienta viene después.

### W2-02
- Lane: `RUMBO_BRAND`
- Identity: `RUMBO IA`
- Claim class: `DEMO`
- Target channels: `LinkedIn`, `X`
- Evidence: `docs/brand/CLAIMS_POLICY_V1.md`
- Copy: DEMO: una IA puede proponer un rango de precio usando supuestos explícitos. La decisión final requiere criterio humano, costos reales y contexto comercial.

## Quarantined / not review-ready
- `W2-03`: historical customer-count claim lacks evidence receipt.
- `W2-04`: historical restaurant outcome lacks customer permission and measured evidence.
- `W2-05`: stale personal-brand item; wrong lane for RUMBO IA.
- `W2-06`: unsupported +38% newsletter benchmark.
- `EP001`: specified but not rendered; remains source material.

## Human review checklist
- [ ] Identity and first mention remain `RUMBO IA`.
- [ ] Claim class is no stronger than evidence.
- [ ] Any DEMO is visibly labeled in-context.
- [ ] CTA is allowed by `CHANNEL_MATRIX_V1.md` / `MESSAGING_V1.md`.
- [ ] No customer/metric/ROI claim was added during editing.
- [ ] Privacy-sensitive information is absent.
- [ ] Reviewer explicitly approves or rejects each item.

A checked review packet is still not an approval receipt or publication receipt. `APPROVED` requires an item-specific receipt that binds the exact copy SHA-256 and target channels. Publication requires a separate authenticated action and readback.
