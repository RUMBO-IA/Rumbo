# RUMBO SIWC Multi-Account Local v0.2.0

Successor to the recovered `RUMBO Agent Reliability Local — SIWC OSS Preview` v0.1.0.

## Purpose

Use multiple **separate ChatGPT account registrations** from a RUMBO-owned local runtime without API keys, credential copying between accounts, or dependence on ChatGPT conversation history. Each registration keeps its issued OpenAI OAuth `client_id`, validated subject and credentials separate while the physical PC keeps one stable `ext_agent_host_id`.

This is an open-source/local Sign in with ChatGPT client. It is not the commercial SIWC product and does not imply OpenAI partner approval.

## Commands

```powershell
node client.mjs signin --label primary
node client.mjs signin --label secondary
node client.mjs list
node client.mjs use <account-id>
node client.mjs status
node client.mjs models
node client.mjs ask --model <slug> "Audit this change"
node client.mjs codex-server
node client.mjs logout
```

For returning authorization of an existing registration:

```powershell
node client.mjs signin --account <account-id>
```

## Security

- First registration uses `dynamic_agent_client`; returning authorization reuses the issued `oaiapp_*` client ID.
- Fresh state, nonce and PKCE S256 for every authorization attempt.
- Callback is loopback `127.0.0.1` only.
- ID tokens are verified with OpenAI JWKS, RS256, issuer, audience, nonce and expiration checks.
- On Windows, access/refresh/ID tokens are stored using **DPAPI CurrentUser**; plaintext tokens are never written to the account index.
- On Unix-like hosts the secret envelope is written with mode `0600`.
- Account metadata and tokens are never merged across registrations.
- `logout` attempts remote refresh-token revocation and then clears local credentials while retaining the registration/client mapping.
- `codex-server` passes only the active account's access token to a child Codex app-server through the process environment; it is not printed.

## Usage truth

ChatGPT Plus plan usage is shared across apps using that same ChatGPT account. Separate ChatGPT accounts remain separate registrations and separate plan allowances; this client does not combine or pool them.

A model catalog is not an entitlement proof. A completed inference verifies that model/account request.

## Tests

```powershell
node --test test.mjs
```

Live OAuth and inference are deliberately not exercised by the unit suite because they require the user's interactive authorization and consume account usage.
