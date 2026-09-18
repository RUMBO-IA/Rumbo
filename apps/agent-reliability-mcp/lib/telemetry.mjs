import { createHmac } from "node:crypto";

export const METRIC_SCHEMA = "rumbo.openai-plugin-adoption-observation/v1";

function metaValue(meta, key) {
  return typeof meta?.[key] === "string" ? meta[key] : null;
}

export function pseudonymize(value, secret) {
  if (!value || !secret) return null;
  return createHmac("sha256", secret).update(value, "utf8").digest("hex").slice(0, 32);
}

export function extractObservationEvent({ toolName, meta }) {
  return {
    toolName: typeof toolName === "string" && toolName ? toolName : "unknown",
    subject: metaValue(meta, "openai/subject"),
    session: metaValue(meta, "openai/session"),
  };
}

export function emitUsageEvent(
  { toolName, meta },
  secret = process.env.RUMBO_ADOPTION_HMAC_SECRET,
) {
  const event = extractObservationEvent({ toolName, meta });
  const record = {
    schema: METRIC_SCHEMA,
    event: "mcp_tool_call",
    tool: event.toolName,
    subject_hash: pseudonymize(event.subject, secret),
    session_hash: pseudonymize(event.session, secret),
    unique_subject_observed: Boolean(event.subject && secret),
  };
  console.log(JSON.stringify(record));
  return record;
}

export function summarizeRecords(records) {
  const users = new Set();
  const sessions = new Set();
  let toolCalls = 0;
  for (const record of records) {
    if (record?.schema !== METRIC_SCHEMA) continue;
    if (record.event !== "mcp_tool_call") continue;
    toolCalls += 1;
    if (record.subject_hash) users.add(record.subject_hash);
    if (record.session_hash) sessions.add(record.session_hash);
  }
  return {
    tool_calls_total: toolCalls,
    observed_active_users: users.size,
    observed_sessions: sessions.size,
  };
}
