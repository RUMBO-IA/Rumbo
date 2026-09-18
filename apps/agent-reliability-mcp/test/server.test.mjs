import test from "node:test";
import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import app from "../index.mjs";

const protocolHeaders = {
  "content-type": "application/json",
  accept: "application/json, text/event-stream",
  "MCP-Protocol-Version": "2025-11-25",
};

test("health endpoint is live", async () => {
  const response = await app.request("http://localhost/healthz");
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { ok: true });
});

test("MCP initialize endpoint responds", async () => {
  const response = await app.request("http://localhost/mcp", {
    method: "POST",
    headers: protocolHeaders,
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2025-11-25",
        capabilities: {},
        clientInfo: { name: "rumbo-test", version: "1.0.0" },
      },
    }),
  });
  assert.ok([200, 202].includes(response.status));
  const text = await response.text();
  assert.match(text, /rumbo-agent-reliability-mcp|RUMBO Agent Reliability/);
});

test("tool execution records OpenAI subject/session after handler execution", async () => {
  const logs = [];
  const originalLog = console.log;
  const previousSecret = process.env.RUMBO_ADOPTION_HMAC_SECRET;
  process.env.RUMBO_ADOPTION_HMAC_SECRET = "test-secret";
  console.log = (value) => logs.push(value);

  try {
    const response = await app.request("http://localhost/mcp", {
      method: "POST",
      headers: protocolHeaders,
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 2,
        method: "tools/call",
        params: {
          name: "rumbo_reliability_context",
          arguments: {},
          _meta: {
            "openai/subject": "subject-test",
            "openai/session": "session-test",
          },
        },
      }),
    });

    assert.equal(response.status, 200);
    const text = await response.text();
    assert.match(text, /RUMBO Agent Reliability v1|Evidence-first execution/);
    assert.equal(logs.length, 1);

    const record = JSON.parse(logs[0]);
    const expectedSubject = createHmac("sha256", "test-secret")
      .update("subject-test", "utf8")
      .digest("hex")
      .slice(0, 32);
    const expectedSession = createHmac("sha256", "test-secret")
      .update("session-test", "utf8")
      .digest("hex")
      .slice(0, 32);

    assert.equal(record.event, "mcp_tool_call");
    assert.equal(record.tool, "rumbo_reliability_context");
    assert.equal(record.subject_hash, expectedSubject);
    assert.equal(record.session_hash, expectedSession);
    assert.equal(logs[0].includes("subject-test"), false);
    assert.equal(logs[0].includes("session-test"), false);
  } finally {
    console.log = originalLog;
    if (previousSecret === undefined) delete process.env.RUMBO_ADOPTION_HMAC_SECRET;
    else process.env.RUMBO_ADOPTION_HMAC_SECRET = previousSecret;
  }
});

test("rejected tool calls emit no adoption event", async () => {
  const logs = [];
  const originalLog = console.log;
  const previousSecret = process.env.RUMBO_ADOPTION_HMAC_SECRET;
  process.env.RUMBO_ADOPTION_HMAC_SECRET = "test-secret";
  console.log = (value) => logs.push(value);

  try {
    const response = await app.request("http://localhost/mcp", {
      method: "POST",
      headers: protocolHeaders,
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 3,
        method: "tools/call",
        params: {
          name: "tool-that-does-not-exist",
          arguments: {},
          _meta: {
            "openai/subject": "rejected-subject",
            "openai/session": "rejected-session",
          },
        },
      }),
    });

    assert.equal(response.status, 200);
    const text = await response.text();
    assert.match(text, /not found|Unknown tool|unknown tool/i);
    assert.equal(logs.length, 0);
  } finally {
    console.log = originalLog;
    if (previousSecret === undefined) delete process.env.RUMBO_ADOPTION_HMAC_SECRET;
    else process.env.RUMBO_ADOPTION_HMAC_SECRET = previousSecret;
  }
});
