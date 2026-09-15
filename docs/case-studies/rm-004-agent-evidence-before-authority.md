# RM-004 — Evidence Before Authority

## Problem

An agent can claim that a task is complete without supplying enough evidence to justify that claim. In an agentic system, statements such as `deployed`, `verified`, or `ready for production` can influence later decisions, so narrative confidence must not become authority by default.

## Design rule

RUMBO Agent Reliability evaluates three surfaces separately:

1. **Claim** — what the agent says is true.
2. **Evidence** — what can actually be demonstrated.
3. **Gate** — what condition or authorization still has to be satisfied.

A positive result is bounded to the scope that was actually proven.

## Negative case: fail closed

```text
claim:
  TASK_COMPLETE=PASS

evidence:
  "Everything worked"

gates:
  [no structured policy]
```

Expected outcome:

```text
NO_GO / UNPROVEN
```

Free-form narrative does not satisfy a named evidence contract or gate policy.

## Positive case: evidence bound to claims

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

Outcome:

```text
GO / PROVEN
```

This means only that the evaluated contract is proven within that scope. It does not grant global deployment, publication, spend, or production authority.

## Runtime evidence

The semantic layer currently documented for this case study was re-verified as:

```text
semantic runtime: V1.3.12 + valtown-adapter.2
runtime IDs:      5/5 PASS
live acceptance:  29/29 PASS
```

## Authority boundary

The global state remains:

```text
PRODUCTION=NO_GO
```

Semantic acceptance does not automatically close governance or production gates. In the current control-plane state, canonical semantic acceptance remains blocked pending the required independent governance/security seat.

## Why this matters

The goal is not to make an agent sound more certain. The goal is to make it possible for another layer to answer, independently:

- What was claimed?
- What evidence exists?
- What remains unproven?
- What authority is still missing?
- What can be promoted without inventing anything?

## Truth boundary

This case study documents a bounded RUMBO Agent Reliability result. It does **not** claim OpenAI endorsement, certification, employment, global production readiness, or closure of all canonical gates.
