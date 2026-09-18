import { createHmac } from "node:crypto";

export const METRIC_SCHEMA = "rumbo.openai-plugin-adoption-observation/v1";
export const TOOL_EVENT_METHOD = "tools/call";

function candidateMessages(body) {
  return Array.isArray(body) ? body : [body];
}

function getMeta(message) {
  return message?.params?._meta ?? message?._meta ?? {};
}

export function extractObservationEvents(body) {
  const events = [];
  for (const message of candidateMessages(body)) {
    if (message?.method !== TOOL_EVENT_METHOD) continue;
    const meta = getMeta(message);
    events.push({
      toolName: typeof message?.params?.name === "string" ? message.params.name : "unknown",
      subject: typeof meta["openai/subject"] === "string" ? meta["openai/subject"] : null,
      session: typeof meta["openai/session"] === "string" ? meta["openai/session"] : null,
    });
  }
  return events;
}

export function pseudonymize(value, secret) {
  if (!value || !secret) return null;
  return createHmac("sha256", secret).update(value, "utf8").digest("hex").slice(0, 32);
}export function emitUsageEvents(body, secret = process.env.RUMBO_ADOPTION_HMAC_SECRET) {
  const events = extractObservationEvents(body);
  for (const event of events) {
    const record = {
      schema: METRIC_SCHEMA,
      event: "mcp_tool_call",
      tool: event.toolName,
      subject_hash: pseudonymize(event.subject, secret),
      session_hash: pseudonymize(event.session, secret),
      unique_subject_observed: Boolean(event.subject && secret),
    };
    console.log(JSON.stringify(record));
  }
  return events.length;
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