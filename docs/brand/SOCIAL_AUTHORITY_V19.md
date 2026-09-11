# RUMBO IA Social Authority V19

Observed: 2026-09-11
Status: AUTHORIZATION_REQUIRED

## Verified state

- YouTube `RUMBO IA / @rumboagi`: publish authority PASS; readback PASS.
- LinkedIn `Sebastián Federico`: account known; `reauth_required=true`.
- X `@RumboAGI`: canonical target; no account connected.
- Metricool brand `6769976`: authenticated; no social networks connected.
- Upload-Post profile `rumboia`: active and configured for LinkedIn + X connection flow.

## Connection flow

A temporary Upload-Post authorization flow for LinkedIn + X was generated for profile `rumboia` with a 48-hour validity window. The bearer URL/token is intentionally not stored in this repository or in receipts.

Automatic opening of the authorization URL was blocked by product security controls before execution. No token was sent to a browser and no external account state changed.

## Authority boundary

Publication authority is not profile-edit authority. Connected tools currently expose YouTube publication/readback but no profile-description mutation for YouTube, LinkedIn or X.

## Completion gate

`DISTRIBUTION=PASS` remains forbidden until LinkedIn and X complete interactive authorization, the resulting bindings are read back, and any intended profile copy is applied through an explicitly authorized profile-edit surface.