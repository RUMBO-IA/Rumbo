# RUMBO Agent Reliability Local — SIWC OSS Preview

Minimal open-source/local client for OpenAI **Sign in with ChatGPT** dynamic registration.

## Why this exists

This is the OSS/local path only. It is not RUMBO's commercial SIWC integration and does not bypass OpenAI's commercial partner process.

OpenAI's current OSS flow starts first-time registration with `client_id=dynamic_agent_client`, uses a stable `ext_agent_host_id`, loopback `127.0.0.1` callback, PKCE + OIDC, and returns an issued `oaiapp_*` client ID for the authorized account/workspace. It can separately request `chatgpt.tokens.use.direct` for eligible ChatGPT-plan inference.

## Run

```bash
node client.mjs signin
node client.mjs status
node client.mjs models
node client.mjs ask --model <slug> "Audit this change."
```

Requirements: Node.js 22+, system browser, eligible ChatGPT account/workspace, available plan usage.

## Security boundary

- no OpenAI API key;
- no client secret;
- tokens stay local;
- loopback is `127.0.0.1`, not `localhost`;
- fresh OAuth state, nonce and PKCE;
- RS256 ID-token signature/issuer/audience/nonce/expiry validation;
- Responses API uses `store:false` and `stream:true`;
- success requires `response.completed`;
- this code does not claim commercial SIWC approval.

## Tests

```bash
node --test test.mjs
```

## Status

Preview v0.1.0. Protocol contract tested locally; live OAuth/inference requires interactive authorization and available ChatGPT-plan usage.
