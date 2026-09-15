# RUMBO Content Execution Attempt R25

Status: factual execution evidence only; not publication authority and not `PUBLISHED`.

Observed on 2026-09-13:
- W1-01 → LinkedIn company `145014017`: PASS; request `70f76acef4fa4291a3508b56c965e447`; job `3ca0d1d01cf5496194e766339d1bba7b`; remote `urn:li:share:7504857153325666304`.
- W1-02 → LinkedIn company `145014017`: PASS; request `5c018496af3e44aebc27312c01440091`; job `8e7cbb2eb78c40f8ae57902d84f42410`; remote `urn:li:share:7504857262453125120`.
- W1-03 → LinkedIn: `BLOCKED_PRE_EFFECT` by Upload-Post monthly quota; no remote effect observed.
- W2-02 → LinkedIn: not attempted after quota discovery.

Reconciled coverage after readback: `8/10` logical targets and `10` physical remote records.
Residual unobserved targets: W1-03 → LinkedIn and W2-02 → LinkedIn.
These residual targets are derived from current observations; they do not rewrite the four-target issuance snapshot recorded by commit `cec887029a78974f23e530772e3bb46b2054ae02`.

Grant lifecycle reconciliation:
- original one-shot expiry: `2026-09-13T12:00:00-03:00`;
- terminal state recorded: `EXPIRED`;
- `scoped_agent_execution_authorized=false`;
- residual scope is evidence only and cannot be reactivated.

Invariants preserved:
- `AUTO_PUBLISH=NO_GO`.
- Base `agent_may_publish=false`.
- Observed effect does not imply canonical publication.
- Expired execution authority does not authorize retries or alternate-provider publication.
