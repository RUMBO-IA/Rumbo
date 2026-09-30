# RUMBO IA — Agents API Tutorial R1

Status: CANDIDATE / NOT EXECUTED BY CAMPAIGN
Purpose: replace the invalid “build a Dots agent” pseudocode tutorial.

## What this is

A minimal tutorial for the actual OpenAI Agents API public beta.

It is NOT:
- a Dots SDK tutorial;
- proof that this account has Dots;
- a zero-cost runtime promise;
- evidence of production readiness.

Agents API usage can incur model/tool/container charges. Under the current RUMBO campaign zero-spend rule, this tutorial is documentation-only until explicit API-spend authority exists.

Primary quickstart:
https://developers.openai.com/api/docs/guides/agents-api/quickstart

## Prerequisites

The official quickstart requires an OpenAI Platform API key with the relevant Agents/Responses permissions. Keep the key outside the agent sandbox.

Python package:

```bash
pip install --upgrade openai
```

## Minimal Python shape

```python
from openai import OpenAI

with OpenAI() as client:
    with client.beta.agents.sessions.create(
        agent={
            "model": "gpt-6-astra",
            "instructions": "Write clean code, run it, and report actual output.",
        },
        environment={"type": "openai_hosted"},
        input="Create a small Python script, run it, and report the actual output.",
        stream=True,
    ) as events:
        for event in events:
            print(event.to_json(indent=None), flush=True)
```

The official SDK adds the Agents beta header automatically.

## Verification rules

Do not equate an idle session with success.
Inspect terminal events such as:
- `agent.session.turn.completed`
- `agent.session.turn.failed`
- `agent.session.turn.cancelled`

A completed turn does not guarantee every tool succeeded. Read the reported execution result and, for external effects, perform independent readback when possible.

## Durable session model

Store the session ID if the application needs to continue the same work. A later message can continue the durable session.

## Campaign-safe demo plan

When API spend is explicitly authorized:
1. create one bounded session;
2. use a harmless sandbox-only task;
3. stream events;
4. record exact model/environment;
5. verify the generated artifact/output;
6. record cost/usage;
7. publish only the observed result.

Until then:
`RUNTIME_DEMO=NOT_EXECUTED`
`EXTERNAL_SPEND_USD=0`
