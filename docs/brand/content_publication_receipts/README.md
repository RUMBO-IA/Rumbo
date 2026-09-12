# Content publication receipts

This directory stores item-specific receipts only after an authenticated publication action and remote readback.

Rules:
- editorial approval and publication authorization are separate prerequisites;
- each receipt binds exact copy SHA-256, approval receipt, publication-authorization receipt and canonical distribution-lock SHA-256;
- every target channel requires one remote record bound to the canonical account identity;
- remote URL/ID, timezone-aware timestamps and `readback_status=PASS` are mandatory;
- planning, drafting, CI, approval or distribution readiness never creates a publication receipt.
