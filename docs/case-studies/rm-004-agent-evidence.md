# RM-004 — Evidence Before Authority

## Problem

An agent can produce a convincing statement about task completion without that statement being sufficiently tied to evidence. In an agentic system, claims such as `deployed`, `verified`, or `production-ready` can influence later decisions, so textual confidence is not enough.

## Principle

RUMBO Agent Reliability separates three surfaces:

1. **claim** — what the agent says is true;
2. **evidence** — what can actually be demonstrated;
3. **gate** — what authorization or condition still remains open.

A positive conclusion is bounded by the evaluated scope. It must not silently become broader authority.

## Negative case

```text
claim:
  TASK_COMPLETE=PASS

evidence:
  "Everything worked"

gates:
  [no structured gate policy]
```

Expected outcome:

```text
NO_GO / UNPROVEN
```

Free-form narrative does not replace named evidence or an explicit gate policy.

## Positive case

```text
claims:
  READY=PASS
  PACKAGE_SHA256=abc123

evidence:
  READY=PASS
  PACKAGE_SHA256=abc123
  TESTS=PASS

gates:
  GATES=NONE
```

Expected outcome:

```text
GO / PROVEN
```

This means only that the evaluated claim/evidence/gate contract is proven within that scope.

## Runtime evidence

The semantic runtime currently documented for this case is:

```text
semantic runtime: V1.3.12 + valtown-adapter.2
runtime IDs:      5/5 PASS
live acceptance:  29/29 PASS
```

## Authority boundary

```text
semantic proof != global production authority
```

Global production remains:

```text
PRODUCTION=NO_GO
```

Canonical acceptance is still subject to external governance gates. This case study does not claim that those gates are closed.

## Why this matters

The goal is not to make an agent sound certain. The goal is to let an independent layer answer:

- What was claimed?
- What evidence exists?
- What is still unproven?
- What authority is still missing?
- What result can be promoted without inventing anything?

## Public-state disclaimer

This document is a technical case study and portfolio artifact. It does not by itself prove global production readiness, third-party approval, OpenAI endorsement, employment, or public Plugin Directory publication.
