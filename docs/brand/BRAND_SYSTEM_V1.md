# RUMBO IA Brand System V1

Status: CANDIDATE — publication and production are separate gates.

## Identity hierarchy
Parent brand/ecosystem: RUMBO.

Primary public expression: RUMBO IA.

Technical namespace: RUMBO-IA. It is not a consumer-facing replacement brand.

Short form: RUMBO after context is established.

Product family convention: RUMBO <Capability>. Offers, products, profiles and technical namespaces must not be promoted to parent-brand status without an explicit canon change.

Founder/personal identity remains separate from the company/product identity surface.

## Machine-readable identity authority
`docs/brand/identity_registry_v1.json` is the machine-readable identity/role registry consumed by the Brand admission guard. This document explains policy; the registry is the executable source for allowed identity-role pairs and explicit non-canonical identities.

Documentation and registry must change together in one reviewed change. Registry absence, unsupported schema, invalid roles, duplicate roles, invalid identity-role bindings, or overlap between canonical and non-canonical identities is fail-closed.

## Negative canon and admission
`Avanza` is explicitly NON_CANONICAL for RUMBO. It must not be generated, inferred, published or promoted as a RUMBO parent or product brand unless a future reviewed canon change explicitly authorizes it.

`RUMBO Labs` is explicitly NON_CANONICAL for RUMBO because an independently operated AI/automation company already uses that public name in an overlapping market. Historical RUMBO references remain evidence only; the token must not be generated, inferred, published or promoted as a current RUMBO identity unless a future reviewed canon change resolves the collision.

Unknown generated names are deny-by-default. Absence from the canon is not authority to invent a new brand.

Every identity token used in generated or publishable material must be classified as one of: PARENT_BRAND, PUBLIC_EXPRESSION, PRODUCT, OFFER, PROFILE, TECH_NAMESPACE, SHORT_FORM.

Admission is fail-closed:
- recognized token in its allowed role/context -> PASS;
- recognized token in the wrong role -> SAFE_STOP;
- unknown candidate brand -> SAFE_STOP;
- explicitly non-canonical token -> SAFE_STOP;
- unknown role -> SAFE_STOP;
- missing/invalid identity registry -> SAFE_STOP;
- product/offer/profile/namespace promoted to parent brand without canon authority -> SAFE_STOP.

A rename or new product identity requires explicit canon change, evidence, review and normal repository governance before publication.

## Canonical public surface and drift boundary
The currently audited production surface is repository-root `index.html`. The files under `apps/landing-publica/` are secondary/candidate public surfaces and MUST NOT be described as production merely because they are deployable. Promotion of a secondary surface requires a separate publication receipt.

All public/candidate HTML surfaces remain inside the Brand Contract scan so unsupported claims, non-canonical identities, aliases, and loss of human-control positioning cannot hide in a secondary surface.

A visually different candidate surface is not a silent token migration. Any promotion of different colors or typography requires an explicit Brand System version change plus publication evidence.

## Core promise
Core promise (ES): IA con control humano para organizar y automatizar operaciones comerciales.

Core promise (EN): Human-controlled AI for organized, automated commercial operations.

## Canonical V1 tokens
The canonical tokens are reconciled from the currently audited root surface:
- bg: #080c12
- panel: #101722
- panel-2: #141e2c
- line: #263246
- text: #f7f9fc
- muted: #9aa8ba
- orange: #ff7a45 — primary brand/CTA
- green: #63ddb0 — verified/positive/live
- blue: #7aa7ff — informational
- red: #ff7b88 — warning/error

## Typography
Default canonical surface: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Arial, sans-serif. Technical evidence may use ui-monospace/monospace. Secondary/candidate typography does not become canonical without an explicit versioned promotion.

## Shape and spacing
Use compact operational layouts; rounded surfaces should remain consistent with the current product language. Default radii: 10, 12, 14, 18, 20, 24, 28px. Prefer spacing increments of 4px.

## Monogram
Until a separately approved logo asset exists, use the current `R` monogram only as a temporary product identifier. Do not imply trademark registration or certification.

## Voice
Operational, concrete, concise, falsifiable. Prefer evidence-backed language. Avoid guaranteed ROI, invented customers/metrics, claims of autonomy where humans supervise decisions, `100% secure`, and production language for demo/pilot states.

## Claim classes
Every externally visible factual performance/state claim must map to one of: BUILT, DEMO, PILOT, PRODUCTION, MEASURED. Promotion to a stronger class requires evidence. MEASURED claims require an identified evidence record; invented percentages or customer outcomes are prohibited.

## Accessibility baseline
Visible keyboard focus; meaningful text labels in addition to color; sufficient contrast; no critical state communicated by color alone; reduced-motion-safe behavior for nonessential animation.

## Governance
BRAND_SPEC_PASS != PUBLICATION_AUTHORITY != PRODUCTION_DEPLOYMENT.
KNOWN_NAME != ALLOWED_ROLE.
UNKNOWN_NAME != NEW_BRAND_AUTHORITY.
NON_CANONICAL_NAME = SAFE_STOP.
SECONDARY_DEPLOYABLE_SURFACE != PRODUCTION_SURFACE.
CI_PASS != PUBLICATION_RECEIPT.

Source reconciliation: canonical issue #72, repository-root audited public surface, README release posture, machine-readable identity registry, and secondary public/candidate surfaces. Future changes must preserve both identity admission and public-surface drift controls.