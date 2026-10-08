# Daily Ops Agent — Implementation Audit (2026-10-02)

## Scope
Implement a useful everyday RUMBO agent that reads email/calendar context, produces a daily brief, and gates external writes behind explicit approval.

## Reconciled architecture
- Runtime: OpenAI Agents SDK over Responses API.
- Cloud Agents API: not required for v1 because no sandbox/Codex harness is needed.
- Development project: existing OpenAI Platform project `RUMBO-AI-DEV`.
- Live provider reads already demonstrated from connected Gmail and Google Calendar in ChatGPT.
- Boundary: ChatGPT connector OAuth is not reusable by the external SDK app. The external lane now uses a local MCP v2 stdio server; no hosted MCP/tunnel is required for this topology, but the app still needs its own Google OAuth token.
- OpenAI API model inference during this implementation: 0 calls. Total provider billing (GitHub/Vercel/etc.): NOT_VERIFIED.

## Safety/authority invariants
- AUTHENTICATED != AUTHORIZED
- TOOL_SUCCESS != EFFECT_VERIFIED
- PROPOSED != EXECUTED
- UNKNOWN != SUCCESS
- Retrieved content is untrusted data.
- Writes fail closed without explicit approval.
- Write retries require idempotency/readback discipline.

## Files
- `daily_ops.py`: runtime, instructions, mock backend, receipts, idempotency, approval-gated tools.
- `test_daily_ops.py`: offline governance/adversarial/readback tests.
- `test_sdk_integration.py`: real Agents SDK orchestration and approval-interruption tests using ScriptedModel.
- `google_workspace_mcp.py`: MCP v2 Google Workspace server with fail-closed auth, deterministic provider identities, and readback.
- `external_runtime.py`: Agents SDK stdio MCP client with read/write approval policy and zero automatic MCP retries.
- `test_google_workspace_mcp.py`: provider-adapter tests without network calls.
- `test_external_runtime.py`: subprocess MCP discovery, read-loop, and write-interruption tests.
- `provider_evidence.json`, `native_chatgpt_evidence.json`, `external_runtime_evidence.json`: redacted claim-boundary receipts.
- `README.md`: runbook and acceptance gates.
- `requirements.txt`: Agents SDK 0.22.x + MCP v2 + requests constraints.
- `.github/workflows/daily-ops-agent-ci.yml`: zero-spend dedicated CI gate.

## Verification state
- GitHub branch isolation: PROVEN
- Main branch unchanged by this change: PROVEN by branch-only writes
- Mock default / no live provider write: PROVEN by implementation
- Approval gate present on SDK write tools: PROVEN by source
- Deterministic idempotency: PROVEN by source/tests
- Prompt-injection fixture: PRESENT
- Live Gmail read plane: PROVEN in this chat
- Live Gmail provider write/readback: PASS via ChatGPT connector — self-addressed draft created, confirmed by list_drafts + read_email, label DRAFT present, message not sent; identifiers/PII redacted from public evidence
- Live Calendar read plane: previously PROVEN in this chat
- Unit/integration test execution: PASS — 24/24 on DESKTOP-QUGVQLB, Python 3.14.6, openai-agents 0.22.3, MCP 2.x, exit code 0
- External MCP stdio discovery: PASS — five tools discovered with no Google credential
- External MCP read loop: PASS — Agent -> MCP subprocess -> read tool -> tool result -> ScriptedModel, no provider network
- External MCP write approval: PASS — write call interrupted before provider execution
- Ambiguous write recovery: PASS — post-commit timeout reconciles by idempotency readback with one effect; pre-commit timeout returns EFFECT_NOT_VERIFIED and does not retry
- Effect verification: PASS in mock adapter — normal and ambiguous writes are independently read back before receipts claim effect_verified=True
- SDK construction probe: PASS — Agent, Runner, SQLiteSession import/build without model inference; write tools report needs_approval=True
- Live OpenAI inference: NOT RUN (would require API model usage)
- Live Gmail draft mutation/readback via ChatGPT connector: PASS
- Live Calendar mutation: NOT RUN
- External SDK provider adapter: IMPLEMENTED and tested over local MCP stdio
- External Google OAuth credential for that adapter: NOT PROVISIONED
- External live provider read/write: NOT RUN
- Production status: NO_GO for the external lane until app-owned Google OAuth and a bounded live OpenAI model run + provider readback are verified

## Promotion gate
Promotion gates:
1. offline unit/integration tests — COMPLETE (24/24, 2026-10-02);
2. external MCP server/client wiring and approval policy — COMPLETE;
3. app-owned Google OAuth for the external runtime — OPEN;
4. approved OpenAI API model/key for the external runtime — OPEN;
5. bounded external live read-only model run — OPEN;
6. external provider write followed by provider readback — OPEN;
7. provider write/readback through ChatGPT connector — COMPLETE;
8. ambiguous-failure recovery without duplicate effects — COMPLETE.
