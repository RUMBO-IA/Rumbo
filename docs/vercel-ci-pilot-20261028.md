# RUMBO Vercel CI portable checks — candidate-only, 2026-10-28

Scope: `RUMBO-IA/Rumbo` (public static site), experimental branch only.

- The public site remains on the existing Vercel project `rumbo-ia-publica`.
- Do **not** edit `vercel.json`, especially `git.deploymentEnabled`.
- The planned branch begins `test/`, excluded from automatic previews by current `vercel.json`.
- This experiment adds a Node-based, read-only policy regression to the **branch only**. It neither changes production code nor substitutes `privacy-gate.yml`, brand, identity or governed merge checks.
- Run: `node --test scripts/ci-pilot/verify-static.test.mjs` (Node 20+). This needs no third-party dependencies.
- Turborepo (`turbo@2.11.7`) is declared for later Vercel CI operation; installation and Turbo CLI execution are **not yet verified**.
- `vercel ci enable` is **not authorized** by this candidate and must not be run before plan/eligibility/cost review. Hobby team commercial restrictions and CI billing remain to be resolved.
- No secrets, API tokens, `npm` postinstall hooks, deployment calls, or network calls in the test.
- Leave the branch unmerged and do not open a PR until the existing GitHub privacy gate implications and all cost/permissions gates are reviewed.

**Gate**: LOCAL_TESTED is separate from VERCEL_CI_PROVEN. A test running locally does not prove a Vercel CI invocation; keep production and existing required CI checks unchanged.
