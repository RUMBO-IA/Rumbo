import { Hono } from "hono";
import { createMcpHandler } from "mcp-handler";
import { z } from "zod";
import { emitUsageEvent } from "./lib/telemetry.mjs";

const mcpHandler = createMcpHandler((server) => {
  server.registerTool(
    "rumbo_reliability_context",
    {
      title: "RUMBO Reliability Context",
      description:
        "Return the public RUMBO reliability contract used by its evidence-first workflows.",
      inputSchema: z.object({}),
      outputSchema: z.object({
        protocol: z.string(),
        purpose: z.string(),
        rules: z.array(z.string()),
      }),
      annotations: {
        readOnlyHint: true,
        openWorldHint: false,
        destructiveHint: false,
      },
    },
    async (_args, ctx) => {
      const output = {
        protocol: "RUMBO Agent Reliability v1",
        purpose: "Evidence-first execution and final-state verification.",
        rules: [
          "Recover authoritative state before changing it.",
          "Reconcile conflicting evidence instead of guessing.",
          "Separate proven facts from inferences and simulations.",
          "Fail closed when lineage or required evidence is unresolved.",
        ],
      };

      emitUsageEvent({
        toolName: "rumbo_reliability_context",
        meta: ctx?.mcpReq?._meta,
      });

      return {
        structuredContent: output,
        content: [{ type: "text", text: JSON.stringify(output) }],
      };
    },
  );
}, {
  serverInfo: { name: "rumbo-agent-reliability-mcp", version: "0.2.0" },
});

const app = new Hono();

app.get("/", (c) =>
  c.json({
    service: "RUMBO Agent Reliability MCP",
    protocol: "MCP Streamable HTTP",
    path: "/mcp",
    telemetry: "privacy-preserving runtime observation",
  }),
);

app.get("/healthz", (c) => c.json({ ok: true }));

app.get("/.well-known/openai-apps-challenge", (c) => {
  const token = process.env.OPENAI_APPS_CHALLENGE_TOKEN;
  if (!token) return c.text("Not Found", 404);
  return c.text(token, 200, { "Cache-Control": "public, max-age=300" });
});

app.all("/mcp", (c) => mcpHandler(c.req.raw));

export default app;
