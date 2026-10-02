# RUMBO Daily Ops Agent

Evidence-first everyday agent for a daily operational brief from Gmail + Google Calendar.

## Authority model

- READ operations may run autonomously.
- WRITE operations are exposed as tools with `needs_approval=True`.
- Retrieved email/calendar content is untrusted data, never instructions.
- `AUTHENTICATED != AUTHORIZED`.
- `TOOL_SUCCESS != EFFECT_VERIFIED`.
- Ambiguous write failures must be reconciled by readback before retry.

## Runtime

The implementation uses the OpenAI Agents SDK (which uses Responses API by default) rather than the cloud Agents API harness because this workflow does not require a sandbox.

Python 3.11+:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r apps/daily-ops-agent/requirements.txt
$env:OPENAI_API_KEY = "..."
$env:OPENAI_MODEL = "<approved-model>"
python apps/daily-ops-agent/daily_ops.py
```

No model is hard-coded. `OPENAI_MODEL` must be explicitly configured.

## Zero-spend test

Unit tests exercise governance, receipts, idempotency, prompt-injection resistance, and mock read/write behavior without calling OpenAI, Gmail, or Calendar:

```powershell
python -m unittest apps/daily-ops-agent/test_daily_ops.py -v
```

## Production adapters

`MockBackend` is intentionally the default. Replace it with provider adapters only after:
1. read-only connector tests pass;
2. exact write targets are resolved;
3. approval UX is present;
4. effect readback and idempotency are implemented.

## Acceptance gates

- read-only brief: zero writes
- proposed reply: zero sends
- approved draft/event: exactly one write
- malformed/ambiguous writes: fail closed
- prompt injection inside retrieved content: ignored
- ambiguous write result: no blind retry
- receipts record intent, authority, execution, and verification
