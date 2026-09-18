import test from "node:test";
import assert from "node:assert/strict";
import { extractObservationEvent, pseudonymize, summarizeRecords } from "../lib/telemetry.mjs";

test("extracts OpenAI subject/session metadata from an executed-tool context", () => {
  const event = extractObservationEvent({
    toolName: "rumbo_reliability_context",
    meta: {
      "openai/subject": "subject-123",
      "openai/session": "session-456",
    },
  });
  assert.deepEqual(event, {
    toolName: "rumbo_reliability_context",
    subject: "subject-123",
    session: "session-456",
  });
});

test("pseudonymization is keyed and deterministic", () => {
  const a = pseudonymize("subject-123", "test-secret");
  const b = pseudonymize("subject-123", "test-secret");
  const c = pseudonymize("subject-123", "other-secret");
  assert.equal(a, b);
  assert.notEqual(a, c);
  assert.equal(pseudonymize("subject-123", ""), null);
});

test("summary counts unique pseudonyms and calls", () => {
  const records = [
    { schema: "rumbo.openai-plugin-adoption-observation/v1", event: "mcp_tool_call", subject_hash: "a", session_hash: "s1" },
    { schema: "rumbo.openai-plugin-adoption-observation/v1", event: "mcp_tool_call", subject_hash: "a", session_hash: "s2" },
    { schema: "rumbo.openai-plugin-adoption-observation/v1", event: "mcp_tool_call", subject_hash: "b", session_hash: "s2" },
    { schema: "other", event: "mcp_tool_call", subject_hash: "c", session_hash: "s3" },
  ];
  assert.deepEqual(summarizeRecords(records), {
    tool_calls_total: 3,
    observed_active_users: 2,
    observed_sessions: 2,
  });
});
