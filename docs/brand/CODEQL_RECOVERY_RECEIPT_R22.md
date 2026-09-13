# RUMBO CodeQL Recovery Receipt R22

Status: CI recovery evidence only. No content authority or publication state change.

- Prior main: `a0e72e4275f3ac185e58d4f0ef417a37559688da`
- Failed CodeQL run: `34750335909`
- Failed job: `103705616020` (`Analyze (python)`)
- Successful sibling job: `103705616099` (`Analyze (actions)`)
- CodeQL extraction/query coverage: 43/43 Python files and 5/5 GitHub Actions files scanned.
- Failure boundary: improved incremental analysis/cache finalization after SARIF generation/upload attempt.
- GitHub diagnostic: next CodeQL analysis will run without improved incremental analysis.
- Source-code security finding causing failure: NOT_OBSERVED.
- Recovery strategy: trigger a fresh governed CI execution without changing the V2 implementation.

Invariants preserved:
- `AUTO_PUBLISH = NO_GO`.
- `agent_may_publish = false`.
- `observations_grant_authority = false`.
- `observations_promote_state = false`.
- `APPROVED=5`; `PUBLISHED=0`.

This receipt records CI recovery provenance only; it does not classify CodeQL as PASS until a subsequent run completes successfully.
