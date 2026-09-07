# RUMBO Agent Reliability — Evidence Before Authority

## Problem

An agent can state that a task is complete without providing enough evidence to justify that conclusion. RUMBO Agent Reliability separates **claim**, **evidence**, and **gate** so a positive conclusion is limited to what is actually proven.

## Negative case

```text
claim:
  TASK_COMPLETE=PASS

evidence:
  "Everything went well"

gates:
  [no structured gate policy]
```

Expected result:

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

Result:

```text
GO / PROVEN
```

This result applies only to the evaluated scope. It does not grant global authority.

## Verified semantic runtime

```text
semantic runtime: V1.3.12 + valtown-adapter.2
runtime IDs:      5/5 PASS
live acceptance:  29/29 PASS
```

## Authority boundary

```text
semantic proof != global production authority
PRODUCTION=NO_GO
```

Canonical acceptance remains subject to external governance gates. PASS does not automatically authorize deployment, spend, publication, or production.

## Publication status

This page is a public technical proof artifact. It does not claim OpenAI endorsement, employment, certification, Plugin Directory approval, or global production readiness.
