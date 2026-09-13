# Content approval receipts

This directory stores item-specific human approval receipts.

Rules:
- A receipt is created only after explicit human approval.
- Automated/agent lanes MUST NOT issue approval receipts (`agent_may_issue_receipts=false`).
- The receipt binds the exact canonical copy with SHA-256.
- `APPROVED` is not `PUBLISHED`.
- Changing copy or target channels invalidates the receipt.
- Publication still requires its own authenticated publication receipt/readback.
- `AUTO_PUBLISH=NO_GO` remains unchanged.
