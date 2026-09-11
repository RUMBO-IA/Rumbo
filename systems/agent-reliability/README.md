# RUMBO Agent Reliability

[![RUMBO Agent Reliability CI](https://github.com/RUMBO-IA/Rumbo/actions/workflows/agent-reliability-ci.yml/badge.svg?branch=main)](https://github.com/RUMBO-IA/Rumbo/actions/workflows/agent-reliability-ci.yml)

**Capability ≠ Authorization ≠ Execution ≠ Verified Outcome**

This is a deliberately small deterministic demonstration of agent-workflow reliability invariants.

It tests seven behaviors: missing authority, successful verified execution, false-success detection, idempotent retry handling, stale-context blocking, missing verification evidence, and verification disagreement.

## Scope

Status: `LOCAL_PROVEN` based on the recorded local run. GitHub CI, when successful, adds a second execution-environment check; it is **not** validation performed by another person.

This system does **not** establish production reliability, distributed correctness, enterprise readiness, or security against arbitrary adversaries.

## Run

From the repository root:

```bash
python -m pip install pytest==9.0.2
PYTHONPATH=systems/agent-reliability/src python -m pytest -q systems/agent-reliability/tests
```

## Seven invariants

1. Missing authority blocks execution.
2. Valid authority + real execution + successful readback yields `VERIFIED`.
3. Executor-reported success without matching state yields `NOT_PROVEN`.
4. A repeated idempotency key cannot create a second side effect.
5. Stale context is blocked unless the request is a legitimate deduplicated retry.
6. Missing verification evidence cannot yield `VERIFIED`.
7. Verification disagreement yields `NOT_PROVEN`.

## Evidence

The local receipt is in [`evidence/receipt.json`](evidence/receipt.json). It explicitly records `production_proven=false` and `external_reproduction=false` for the original local artifact.

## Limitations

See [`docs/limitations.md`](docs/limitations.md). Claims are intentionally narrower than the implementation ambitions.
