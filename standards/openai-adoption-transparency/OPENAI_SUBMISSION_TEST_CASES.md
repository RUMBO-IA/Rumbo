# OpenAI MCP submission test cases

These cases are prepared for the public-plugin submission form. They describe expected behavior; they do not claim that OpenAI has approved or executed them.

## Positive cases

### P01 — Initialize
Send a valid MCP initialize request using a supported protocol version.
Expected: the server initializes successfully and identifies the RUMBO Agent Reliability MCP server.

### P02 — Discover tools
Complete initialization and request the advertised tools.
Expected: rumbo_reliability_context is present with an input schema, output schema, and read-only/non-destructive annotations.

### P03 — Execute read-only tool
Call rumbo_reliability_context with an empty arguments object.
Expected: HTTP/MCP success and a structured result matching the declared output schema.

### P04 — Execute with OpenAI metadata
Call the same tool with _meta["openai/subject"] and _meta["openai/session"].
Expected: the tool succeeds; telemetry records only HMAC pseudonyms, never the raw metadata values.

### P05 — Repeated execution aggregation
Execute the tool twice with the same subject and different sessions.
Expected: two tool calls are counted while the subject cardinality remains one.

## Negative cases

### N01 — Unknown tool
Call a tool name that is not registered and include synthetic subject/session metadata.
Expected: the request is rejected and no adoption event is emitted.

### N02 — Malformed JSON
Send invalid JSON to the MCP endpoint.
Expected: the request is rejected before tool execution and no adoption event is emitted.

### N03 — Unsupported protocol version
Send a tools/call request with an unsupported MCP-Protocol-Version.
Expected: the request is rejected before tool execution and no adoption event is emitted.

## Evidence rule
A passing local case proves only local implementation behavior. Production execution and OpenAI review remain separate evidence states.