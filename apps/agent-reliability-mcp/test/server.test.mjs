import test from "node:test";
import assert from "node:assert/strict";
import app from "../index.mjs";

test("health endpoint is live", async () => {
  const response = await app.request("http://localhost/healthz");
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { ok: true });
});

test("MCP initialize endpoint responds", async () => {
  const response = await app.request("http://localhost/mcp", {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json, text/event-stream" },
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