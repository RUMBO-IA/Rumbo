# Content publication authorization receipts

This directory stores explicit human authorization to execute publication for an already approved content item.

Rules:
- authorization is item-specific and binds exact copy SHA-256, approval receipt and target channels;
- `APPROVED` does not imply publication authorization;
- automated/agent lanes must not issue these receipts;
- publication still requires a later authenticated action and per-channel readback receipt.
