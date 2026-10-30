# RUMBO Vercel CI portable checks — candidate-only, 2026-10-28

Scope: `RUMBO-IA/Rumbo` (public static site), experimental branch only.

- The public site remains on the existing Vercel project `rumbo-ia-publica`.
- Do **not** edit `vercel.json`, especially `git.deploymentEnabled`.
- The proposed review branch begins `test/`, excluded from automatic previews by current `vercel.json`; keep this verified before changing branch names.
- This experiment adds a Node-based, read-only policy regression to the **branch only**. It neither changes production code nor substitutes `privacy-gate.yml`, brand, identity or governed merge checks.
- Run: `node --test scripts/ci-pilot/verify-static.test.mjs` (Node 20+). This needs no third-party dependencies.
- No root `package.json`, package-lock or `turbo.json` is introduced. The Node `.mjs` regression has no third-party dependency or Vercel build impact. This does **not** establish eligibility for Vercel CI.
- `vercel ci enable` is **not authorized** by this candidate and must not be run before plan/eligibility/cost review. Hobby team commercial restrictions and CI billing remain to be resolved.
- No secrets, API tokens, `npm` postinstall hooks, deployment calls, or network calls in the test.
- Existing PR remains DRAFT / UNMERGED until GitHub privacy, deployment cost and authorization gates are reviewed. Do not enable Vercel CI or production deployment.

**Gate**: LOCAL_TESTED is separate from VERCEL_CI_PROVEN. A test running locally does not prove a Vercel CI invocation; keep production and existing required CI checks unchanged.
