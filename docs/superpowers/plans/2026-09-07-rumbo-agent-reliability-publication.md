# RUMBO Agent Reliability Public Publication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce one exact, locally verified, reviewer-ready skills-only publication packet for `RUMBO Agent Reliability`, without submitting or publishing it.

**Architecture:** Recover the existing `0.1.6` five-skill package from its proven Git lineage, bind every source byte by SHA-256, and copy only the approved skills-only tree into a publication candidate. Add a standalone verifier plus reviewer packet; portal/account writes remain fail-closed external gates.

**Tech Stack:** Git, Python 3.11+, JSON, Markdown, OpenAI plugin skills-only package format.

**Spec:** `docs/superpowers/specs/2026-09-07-rumbo-agent-reliability-publication-design.md`

## Global Constraints

- First public candidate is `RUMBO Agent Reliability`; `rumbo-workflow-suite` remains second phase.
- Package slug remains `rumbo-coding-agent-reliability`, recorded distribution version `0.1.6`.
- Exact skills: `canonical-state-recovery`, `deep-research-reconcile`, `goal-loop-controller`, `execute-verify-close`, `audit-final-state`.
- No `.app.json`, `.mcp.json`, MCP server, hooks, hidden network dependency, billing, write action, or auth flow.
- No portal submission, approval, publication, or directory-presence claim from local verification.
- Public publisher URLs must return HTTP 200 immediately before portal entry.
- Portal mutation requires verified Developer Identity and Apps Management write authority.

---### Task 1: Bind the Proven 0.1.6 Source

**Files:**
- Create: `openai-publication/agent-reliability/source-receipt.json`
- Create: `scripts/test_verify_agent_reliability_publication.py`
- Create: `scripts/verify_agent_reliability_publication.py`

**Interfaces:**
- Consumes: Git commit `3a7bff2a139cb6840ab6e23a2c19e315000e8b13` and `plugins/rumbo-coding-agent-reliability/`.
- Produces: `source-receipt.json` with commit/tree/manifest/five-skill SHA-256 bindings.

- [ ] **Step 1: Write a failing test** requiring the receipt to name the exact commit, exact five skills, and SHA-256 for manifest + every skill.
- [ ] **Step 2: Run** `python -m unittest scripts.test_verify_agent_reliability_publication.SourceBindingTests -v`; expect failure because publication files do not exist.
- [ ] **Step 3: Implement minimal verifier and source receipt** using raw `git show <sha>:<path>` bytes; never normalize line endings before hashing.
- [ ] **Step 4: Run the focused test** and require PASS.
- [ ] **Step 5: Commit** `test/feat(openai): bind agent reliability publication source`.

### Task 2: Materialize the Skills-Only Candidate

**Files:**
- Create: `openai-publication/agent-reliability/plugin/.codex-plugin/plugin.json`
- Create: five `openai-publication/agent-reliability/plugin/skills/*/SKILL.md`
- Create: `openai-publication/agent-reliability/plugin/assets/icon.svg`
- Create: `openai-publication/agent-reliability/plugin/assets/logo.svg`
- Modify: `scripts/test_verify_agent_reliability_publication.py`

**Interfaces:** Candidate bytes must match the source receipt for the five skills; manifest may change only where publication metadata is explicitly audited.
- [ ] **Step 1: Add failing inventory tests** for exactly five skills, required manifest, two SVG assets, and forbidden executable/network/auth components.
- [ ] **Step 2: Run focused inventory tests**; expect failure because candidate is absent.
- [ ] **Step 3: Copy exact source bytes** from the bound Git commit; update only metadata required by the approved public listing and record any manifest delta explicitly.
- [ ] **Step 4: Run inventory, byte-identity, JSON/schema, placeholder, secret-pattern, and forbidden-component tests**; require PASS.
- [ ] **Step 5: Commit** `feat(openai): materialize agent reliability skills-only candidate`.

### Task 3: Build Reviewer Materials and Routing Evals

**Files:**
- Create: `openai-publication/agent-reliability/submission/listing.json`
- Create: `openai-publication/agent-reliability/submission/reviewer-cases.json`
- Create: `openai-publication/agent-reliability/submission/release-notes.md`
- Modify: `scripts/test_verify_agent_reliability_publication.py`

**Interfaces:** `listing.json` provides name/descriptions/category/publisher URLs/starter prompts/availability state; `reviewer-cases.json` provides >=5 positive and >=3 negative cases.

- [ ] **Step 1: Add failing reviewer-packet tests** for 3+ starter prompts, 5+ positive cases, 3+ negative cases, no public-approval claims, and fail-closed availability.
- [ ] **Step 2: Run reviewer tests**; expect failure because packet is absent.
- [ ] **Step 3: Write minimal reviewer packet** grounded in the five approved workflows and public RUMBO publisher surfaces.
- [ ] **Step 4: Run routing/reviewer tests** and require all cases PASS.
- [ ] **Step 5: Commit** `feat(openai): add agent reliability reviewer packet`.

### Task 4: Full Verification and Account-Gate Receipt

**Files:**
- Create: `openai-publication/agent-reliability/FINAL_READINESS.json`
- Modify: `scripts/verify_agent_reliability_publication.py`
- Modify: `scripts/test_verify_agent_reliability_publication.py`
**Interfaces:** Final verifier emits one machine-readable readiness verdict; account gates remain separate observations.

- [ ] **Step 1: Add failing final-state tests** requiring package verification, public URL readback fields, account-gate fields, and explicit `submitted=false`, `published=false`.
- [ ] **Step 2: Run final-state tests**; expect failure until receipt exists.
- [ ] **Step 3: Implement final verifier** to hash the candidate, run all local checks, and consume explicit account/public-URL observations without fabricating them.
- [ ] **Step 4: Run** `python -m unittest scripts.test_verify_agent_reliability_publication -v`, repository privacy tests, `git diff --check`, and the publication verifier; require all PASS.
- [ ] **Step 5: Re-read website/support/privacy/terms over HTTPS** and record exact status/readback evidence.
- [ ] **Step 6: Query available OpenAI account/plugin surfaces** for current installed/public state and permission evidence; unresolved Apps Management/Developer Identity remains `OPEN`, not guessed.
- [ ] **Step 7: Commit** `test(openai): close agent reliability publication readiness`.

### Task 5: Integration Gate

**Files:** No new product files unless verification finds a material defect.

**Interfaces:** Exact branch head is the only candidate eligible for review/integration.

- [ ] **Step 1: Run complete fresh verification** from a clean worktree.
- [ ] **Step 2: Push the isolated branch through the approved host Git path** only after privacy/identity hooks pass.
- [ ] **Step 3: Require exact-head CI green** and inspect changed-file scope.
- [ ] **Step 4: Use Safe Merge Authority dry-run** before any merge decision; do not merge merely because CI is green.
- [ ] **Step 5: Stop before `Submit for Review`** unless current account gates are proven and explicit submission authority is separately present.

## Self-review

- Spec coverage: source binding, five-skill package, listing, reviewer cases, safety boundary, URL readback, account gates, state machine, and external-effect separation are all mapped above.
- Placeholder scan: plan contains no implementation placeholders; unresolved external observations are deliberately fail-closed runtime gates.
- Type/name consistency: `source-receipt.json`, `listing.json`, `reviewer-cases.json`, and `FINAL_READINESS.json` are stable across tasks.