# OpenAI DevDay 2026 — RUMBO IA Builder Brief R1

Status: CANDIDATE / PRIMARY-SOURCE-BOUND / NO AUTO DELIVERY
Observed: 2026-09-29

## The useful separation

### Dots
Dots are an OpenAI product for ongoing delegated work. OpenAI describes them as always-on agents powered by GPT-6 Astra with their own cloud computer/browser and plugin connections.

Availability is a product/plan/market/admin question. Do not infer account entitlement from a public announcement.

Primary:
- https://openai.com/index/introducing-dots/
- https://openai.com/index/devday-2026-recap/

### Agents API
Agents API is a developer API, not a Dots SDK.

OpenAI manages sessions, orchestration, context compaction, and recovery. Your application supplies tools/workflow and chooses an execution environment.

Core objects:
- Agent
- Environment
- Session
- Events/items

Agents API supports OpenAI-hosted or self-hosted environments, MCP connections, and subagents.

Primary:
- https://developers.openai.com/api/docs/guides/agents-api/overview
- https://developers.openai.com/api/docs/guides/agents-api/quickstart

### GPT-6.1 Sol
GPT-6.1 Sol is a model, not an agent product.

Current standard API pricing per 1M tokens:
- input: USD 2.00
- cached input: USD 0.10
- cache writes: USD 2.50
- output: USD 10.00

Primary:
- https://developers.openai.com/api/docs/models/gpt-6.1-sol

## RUMBO reliability lens

For any agentic workflow ask:

1. What authority does it actually have?
2. What state was verified immediately before execution?
3. What receipt proves the external action happened?
4. What happens after interruption or partial failure?
5. Can another path independently read back the effect?

`REQUEST_ACCEPTED != EFFECT_VERIFIED`
`ANNOUNCED != ACCOUNT_ENTITLED`
`SESSION_COMPLETED != EVERY_TOOL_SUCCEEDED`

## CTA

RUMBO IA DevDay Builder Brief priority list:
https://form.typeform.com/to/T8Qi1DS4

This form is a waitlist/prioritization signal. It is not an automatic download or guaranteed delivery date.

## Publication boundary

Use this brief as the source for campaign derivatives only after fresh primary-source verification.
No paid API run, Dots entitlement claim, customer result, production claim, or ROI claim is implied.
