/**
 * Read-only policy checks. Not a substitute for RUMBO brand/privacy/security
 * gates, runtime validation, trusted-runner checks, or governed merge checks.
 * Pure function deliberately kept free of network, env, deployment, and writes.
 */
export function evaluateStaticPolicy(config, requiredPaths = []) {
  const failures = [];
  const fail = (code) => failures.push(code);

  const deployment = config?.git?.deploymentEnabled;
  if (deployment?.main !== false) fail('MAIN_AUTODEPLOY_NOT_DISABLED');
  if (deployment?.['test/*'] !== false) fail('TEST_BRANCH_AUTODEPLOY_NOT_DISABLED');

  const root = (Array.isArray(config?.headers) ? config.headers : [])
    .find((item) => item?.source === '/(.*)');
  const headers = new Map((Array.isArray(root?.headers) ? root.headers : [])
    .filter((item) => typeof item?.key === 'string' && typeof item?.value === 'string')
    .map((item) => [item.key.toLowerCase(), item.value]));

  const csp = headers.get('content-security-policy') || '';
  for (const directive of ["default-src 'self'", "frame-ancestors 'none'", "object-src 'none'", "base-uri 'none'"]) {
    if (!csp.split(';').some((s) => s.trim() === directive)) fail(`CSP_REQUIRED_DIRECTIVE_MISSING:${directive}`);
  }
  if (csp.includes("'unsafe-eval'")) fail('CSP_UNSAFE_EVAL');
  if (headers.get('x-content-type-options') !== 'nosniff') fail('NOSNIFF_MISSING');
  if (headers.get('x-frame-options') !== 'DENY') fail('X_FRAME_OPTIONS_NOT_DENY');
  if (!String(headers.get('strict-transport-security') || '').includes('max-age=')) fail('HSTS_MISSING');

  const redirects = Array.isArray(config?.redirects) ? config.redirects : [];
  if (!redirects.some((r) => r?.source === '/apps/landing-publica' && r?.destination === '/' && r?.permanent === true)) {
    fail('CANONICAL_REDIRECT_MISSING');
  }

  const paths = new Set(requiredPaths);
  for (const path of ['index.html', 'privacy.html', 'security.html', 'robots.txt']) {
    if (!paths.has(path)) fail(`REQUIRED_PUBLIC_FILE_MISSING:${path}`);
  }

  return failures;
}
