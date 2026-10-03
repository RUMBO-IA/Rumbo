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
python -m unittest discover -s apps/daily-ops-agent -p "test*.py" -v
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
- ambiguous write result: read back by idempotency key; never blind retry
- write receipts require a separate state check before claiming confirmation
- pre-commit timeout remains `EFFECT_NOT_VERIFIED` with zero retry
- receipts record intent, authority, execution, and verification

## External Google Workspace MCP runtime

The external Agents SDK path is now implemented with a local MCP v2 server:

```text
external_runtime.py
    -> MCPServerStdio
    -> google_workspace_mcp.py
    -> Gmail REST / Google Calendar REST
```

Provider credentials are not copied from ChatGPT. The external application must provide its own Google OAuth access token:

```powershell
$env:GOOGLE_OAUTH_ACCESS_TOKEN = "<app-owned-google-oauth-token>"
$env:OPENAI_API_KEY = "<openai-project-key>"
$env:OPENAI_MODEL = "<approved-model>"
```

Minimum practical Google scopes for this implementation:

```text
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/calendar.events
```

Writes are disabled by default. Enable the server-side write plane only for an intentionally authorized run:

```powershell
$env:RUMBO_ALLOW_WRITES = "1"
```

The Agents SDK still requires approval for `gmail_create_draft` and `calendar_create_event`. The MCP client is configured with `max_retry_attempts=0`; ambiguous writes reconcile by deterministic provider identity plus readback.

Offline discovery without credentials:

```powershell
python apps/daily-ops-agent/external_runtime.py
```

Expected tool surface:

```text
calendar_create_event
calendar_events
gmail_create_draft
gmail_read
gmail_search
```

The external runtime is implementation-ready but not live-authorized until the app owns a Google OAuth token and an approved OpenAI API model/key.
