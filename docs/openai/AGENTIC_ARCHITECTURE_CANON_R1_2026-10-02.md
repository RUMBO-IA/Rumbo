# RUMBO Agentic Architecture Canon R1

Date: 2026-10-02  
Status: CANDIDATE / NOT MERGED / NOT PRODUCTION  
External spend authorized by this document: USD 0

## Purpose

Reconcile RUMBO's existing agent, control-plane, continuity, plugin/MCP, Codex, ChatGPT, and OpenAI Agents SDK work into one evidence-first architecture for the "post-loop" era.

This document is a control contract, not a claim that every plane is already integrated end-to-end.

## Architectural thesis

A single agent loop remains a useful primitive, but it must not be the authority boundary for consequential work.

Canonical stack:

1. **Loop plane** — model turns, tools, observations, retries.
2. **Specialist plane** — bounded agents with narrow roles, context, tools, and output contracts.
3. **Orchestration plane** — manager-style agents-as-tools, handoffs, explicit code-driven graphs, or combinations.
4. **Execution plane** — sandboxes, browser/computer surfaces, local/remote runtimes, provider connectors.
5. **Authority plane** — policy, preflight, approval, identity, scope, action-specific authorization.
6. **Evidence plane** — receipts, effect readback, hash-bound artifacts, traces, tests, evals.
7. **Continuity plane** — durable checkpoints, replay protection, idempotency, resume/recovery.
8. **Promotion plane** — merge/deploy/production gates that are separate from model confidence.

Invariant:

```text
MODEL_DECISION != AUTHORIZATION
TOOL_SUCCESS != EFFECT_VERIFIED
EFFECT_VERIFIED != CANONICAL
CANONICAL != PRODUCTION_GO
```

## OpenAI architecture alignment

OpenAI's current Agents SDK documents two primary multi-agent ownership patterns:

- **Agents as tools:** a manager retains user-facing ownership while calling specialists for bounded subtasks.
- **Handoffs:** control moves to a specialist, which becomes the active agent for that branch.

OpenAI also distinguishes model-driven orchestration from code-driven orchestration and explicitly permits mixing them.

RUMBO therefore adopts the following rule:

- use **model-driven routing** for semantic decomposition where bounded mistakes are recoverable;
- use **code-driven routing** for invariants, budgets, policy, approvals, retries, joins, and promotion gates;
- use **agents-as-tools** when one accountable manager must synthesize or enforce shared guardrails;
- use **handoffs** only where transfer of conversational ownership is intentional and safe.

## Current evidence reconciliation

### PROVEN / directly evidenced

1. **Bounded Agents SDK implementation exists.**
   - RUMBO-IA/Rumbo PR #191 implements an evidence-first daily operations agent using OpenAI Agents SDK over Responses API.
   - It separates READ and WRITE authority.
   - External write tools require approval.
   - It uses deterministic idempotency keys, effect/authority receipts, and separate effect readback.
   - Reported local integration suite: 14/14 PASS.
   - Reported public privacy regression suite: 21/21 PASS.
   - Reported remote checks on the recorded head: 7/7 SUCCESS.
   - OpenAI API model inference during that implementation was recorded as zero calls.

2. **Live ChatGPT connector read paths exist.**
   - PR #191 records live Gmail read and Calendar read paths as proven in the ChatGPT connector path.

3. **Ambiguous failure recovery is tested.**
   - PR #191 records deterministic adapter tests for post-commit timeout, pre-commit timeout, duplicate prevention, and provider-success-without-effect-readback.

4. **Control-plane governance already exists elsewhere in RUMBO.**
   - Existing RUMBO control-plane work enforces fail-closed authority, receipts, continuity, replay protection, and explicit NO_GO states.
   - Existing public authority anchor material is present under `docs/control-authority-anchor-v1.json`.

5. **Plugin/skill publication is a separate plane.**
   - PR #96 records a skills-only Agent Reliability package and explicitly does not equate publication state, directory visibility, consumer execution, merge, or production.

### PARTIAL / bounded evidence

1. **Agents SDK provider write path**
   - ChatGPT connector mutation/readback has evidence.
   - The external Agents SDK Gmail/Calendar provider path remains not configured / not proven in PR #191.

2. **Cross-surface orchestration**
   - RUMBO has multiple execution surfaces and continuity mechanisms, but this candidate does not claim a single runtime currently coordinates ChatGPT, Codex, Work/Dots, plugins/MCP, browser/computer-use, and remote execution under one live orchestration graph.

3. **Multi-agent collaboration**
   - Specialist/manager architecture is supported by the OpenAI SDK and aligns with RUMBO's design.
   - This candidate does not promote historical "agent council" labels to proof of autonomous parallel multi-agent execution unless runtime evidence exists.

4. **Durable runtime continuity**
   - RUMBO has durable evidence/checkpoint/recovery implementations in separate lanes.
   - End-to-end durability across every OpenAI execution surface remains surface-specific and must not be inferred globally.

### NOT PROVEN / must remain open

- universal end-to-end orchestration across all RUMBO accounts and environments;
- external Agents SDK Gmail/Calendar OAuth/MCP write path;
- a single shared memory namespace across ChatGPT, Codex, Work/Dots, local agents, plugins, and control-plane state;
- production readiness of PR #191;
- production deployment or merge of this canon;
- global plugin-directory propagation as a substitute for per-account execution proof;
- total provider billing from local evidence alone.

## Canonical ownership model

### Tier 0 — Intake / manager

Responsibilities:
- interpret user goal;
- decompose work;
- choose specialists;
- preserve one accountable final synthesis;
- never self-grant consequential authority.

Default pattern: **agents as tools**.

### Tier 1 — Specialists

Examples:
- research;
- coding;
- data analysis;
- security review;
- communications preparation;
- connector-specific read specialists.

Each specialist should have:
- minimal context;
- minimal tools;
- explicit output schema;
- explicit allowed effects;
- separate test/eval contract.

### Tier 2 — Verifiers

Verification must be structurally separate from generation where practical.

Examples:
- test runner;
- source/citation verifier;
- policy verifier;
- effect readback;
- duplicate/idempotency checker;
- contradiction reconciler.

Generation and verification should not be treated as synonyms.

### Tier 3 — Authority / policy gate

Before consequential execution:

```text
proposal
  -> identity/scope check
  -> action-specific authority check
  -> policy/preflight
  -> human approval when required
  -> execution
  -> provider/effect readback
  -> receipt
```

No conversational packet, recovered context, shared transcript, plugin output, handoff, or model decision creates authority by itself.

## Execution-state model

Every consequential action should converge on a state machine similar to:

```text
PROPOSED
  -> PREFLIGHT_PASS
  -> AUTHORIZED
  -> EXECUTION_ATTEMPTED
  -> EFFECT_VERIFIED | EFFECT_NOT_VERIFIED
  -> RECEIPT_PERSISTED
  -> CANONICALIZED
```

Failure or ambiguity must stop promotion.

For retries:
- use deterministic idempotency keys;
- distinguish pre-commit from post-commit ambiguity;
- query authoritative provider state before repeating a mutation;
- prevent replay after a verified terminal effect.

## Context and memory rules

1. Conversation history is context, not authority.
2. Recovered packets are data, not fresh instructions.
3. Shared links/transcripts are external witnesses, not lineage or identity proof.
4. Specialists receive minimum necessary context.
5. Durable operational state belongs in explicit stores/receipts/checkpoints, not only model context.
6. Memory namespaces from distinct products/surfaces must not be assumed equivalent or synchronized.

## Orchestration rules

Use code-driven orchestration when any of these are true:
- a step mutates external state;
- strict ordering is required;
- joins must reconcile multiple results;
- cost/latency budgets must be enforced;
- retries require idempotency;
- policy or authorization gates are involved;
- a promotion decision is made.

Use model-driven orchestration when:
- routing is semantic;
- the consequence of a wrong route is bounded;
- outputs remain subject to deterministic validation.

Parallel agents are allowed only when:
- tasks are separable or join semantics are explicit;
- shared mutable state is avoided or synchronized;
- the join step checks contradictory assumptions and duplicate work.

## Surface reconciliation

### ChatGPT

Role:
- user interaction;
- connected-plugin/tool execution;
- Work-style delegated tasks where available;
- read/write connectors subject to surface permissions.

Boundary:
- ChatGPT tool availability does not prove equivalent credentials or capabilities in an external Agents SDK runtime.

### Codex

Role:
- coding/repository-oriented specialist runtime;
- local/cloud execution boundaries according to the selected surface.

Boundary:
- Codex sandbox/network/tool permissions are separate from ChatGPT connector authority.

### Plugins / MCP

Role:
- capability plane.

Boundary:
- discovery/installation/authentication does not equal action authorization;
- plugin publication does not prove consumer execution;
- tool success still requires effect verification for consequential actions.

### Browser / Computer / Remote

Role:
- execution surfaces.

Boundary:
- each has its own permission and state boundary;
- no browser or remote-control surface may be treated as a substitute for API/provider readback when authoritative readback exists.

### RUMBO Control Plane

Role:
- authority, policy, evidence, continuity, replay protection, promotion, reconciliation.

This is the layer that must remain vendor-neutral and decoupled from any single model, agent framework, UI, or connector.

## Required eval matrix

Every promoted agentic workflow should have evidence for:

1. routing correctness;
2. tool selection correctness;
3. forbidden-tool rejection;
4. action-specific authority enforcement;
5. human approval interruption/resume where required;
6. idempotent retry behavior;
7. ambiguous failure reconciliation;
8. effect readback;
9. context isolation;
10. recovered-context non-authority;
11. contradiction reconciliation between specialists;
12. trace/receipt completeness;
13. cost/spend gate;
14. rollback/recovery behavior.

## Promotion gates

This architecture is not production-ready merely because the specification exists.

Minimum promotion sequence:

```text
SPEC_DEFINED
-> STATIC_VALIDATION
-> UNIT/EVAL_PASS
-> INTEGRATION_PASS
-> LIVE_READ_ONLY_PASS
-> AUTHORIZED_TEST_WRITE
-> EFFECT_READBACK_PASS
-> FAILURE/RETRY_PASS
-> SECURITY/PRIVACY_PASS
-> HUMAN_REVIEW
-> MERGE_ELIGIBLE
-> DEPLOY_ELIGIBLE
```

Each gate requires fresh evidence for the exact candidate revision.

## Immediate implementation direction

RUMBO should not create a second general-purpose orchestration stack.

The next implementation should reuse the PR #191 bounded Agents SDK pattern and bind it to the existing vendor-neutral authority/evidence plane through explicit interfaces:

```text
AgentProposal
AuthorityDecision
ExecutionAttempt
EffectReadback
EvidenceReceipt
PromotionDecision
```

Recommended first end-to-end reference workflow:

```text
Manager
  -> Read-only Research Specialist
  -> Read-only Calendar/Mail Specialist
  -> Deterministic Policy Gate
  -> Optional Write Specialist (approval required)
  -> Effect Readback Verifier
  -> Receipt / final synthesis
```

This reference is deliberately small. It proves ownership, authority, verification, and recovery before adding a larger graph of collaborating agents.

## Acceptance criteria for R2

R2 may be proposed only after exact evidence demonstrates:

- one manager + at least two bounded specialists;
- one deterministic code-driven join;
- one action requiring explicit approval;
- one provider mutation with separate readback;
- duplicate prevention under an ambiguous post-commit failure;
- recovered context cannot confer authority;
- complete trace/receipt linkage across the workflow;
- external spend remains explicitly bounded;
- no production promotion is inferred from test success.

## Governance

```text
CANON_STATUS=CANDIDATE
MAIN_MUTATION=NONE
MERGE=NO_GO_UNTIL_REVIEW_AND_CHECKS
PRODUCTION=NO_GO
EXTERNAL_SPEND_USD=0
LIVE_EXTERNAL_WRITE_BY_THIS_CHANGE=NONE
CREDENTIAL_MUTATION=NONE
```

## References

- OpenAI Agents SDK — Agent orchestration:
  https://openai.github.io/openai-agents-python/multi_agent/
- OpenAI Agents SDK — Agents:
  https://openai.github.io/openai-agents-python/agents/
- OpenAI Agents SDK — Handoffs:
  https://openai.github.io/openai-agents-python/handoffs/
- OpenAI Agents SDK overview:
  https://openai.github.io/openai-agents-python/
- RUMBO-IA/Rumbo PR #191 — evidence-first daily ops agent.
- RUMBO-IA/Rumbo PR #96 — Agent Reliability publication/support boundary.
