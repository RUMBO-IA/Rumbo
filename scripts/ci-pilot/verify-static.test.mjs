import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { evaluateStaticPolicy } from './verify-static.mjs';

const root = process.cwd();
const config = JSON.parse(readFileSync(resolve(root, 'vercel.json'), 'utf8'));
const requiredPaths = ['index.html', 'privacy.html', 'security.html', 'robots.txt'];
const existingPaths = requiredPaths.filter((path) => existsSync(resolve(root, path)));
const clone = (value) => JSON.parse(JSON.stringify(value));

const mustDetect = (code, modifyConfig, paths = existingPaths) => {
  const changed = clone(config);
  modifyConfig(changed);
  assert.ok(evaluateStaticPolicy(changed, paths).includes(code), `Expected fail-closed signal ${code}`);
};

test('baseline: current public policy and root files pass', () => {
  assert.deepEqual(evaluateStaticPolicy(config, existingPaths), []);
});
test('reject enabling automatic main deploys', () => {
  mustDetect('MAIN_AUTODEPLOY_NOT_DISABLED', (cfg) => { cfg.git.deploymentEnabled.main = true; });
});
test('reject enabling automatic test-branch deploys', () => {
  mustDetect('TEST_BRANCH_AUTODEPLOY_NOT_DISABLED', (cfg) => { delete cfg.git.deploymentEnabled['test/*']; });
});
test('reject missing frame-ancestors CSP directive', () => {
  mustDetect("CSP_REQUIRED_DIRECTIVE_MISSING:frame-ancestors 'none'", (cfg) => {
    const csp = cfg.headers[0].headers.find((h) => h.key === 'Content-Security-Policy');
    csp.value = csp.value.replace("frame-ancestors 'none';", '');
  });
});
test('reject unsafe-eval CSP', () => {
  mustDetect('CSP_UNSAFE_EVAL', (cfg) => {
    const csp = cfg.headers[0].headers.find((h) => h.key === 'Content-Security-Policy');
    csp.value += "; script-src 'unsafe-eval'";
  });
});
test('reject disabled X-Frame-Options', () => {
  mustDetect('X_FRAME_OPTIONS_NOT_DENY', (cfg) => {
    cfg.headers[0].headers.find((h) => h.key === 'X-Frame-Options').value = 'SAMEORIGIN';
  });
});
test('reject missing canonical redirect', () => {
  mustDetect('CANONICAL_REDIRECT_MISSING', (cfg) => { cfg.redirects = []; });
});
test('reject missing public entry point', () => {
  assert.ok(evaluateStaticPolicy(config, existingPaths.filter((x) => x !== 'index.html')).includes('REQUIRED_PUBLIC_FILE_MISSING:index.html'));
});
test('reject missing privacy policy file', () => {
  assert.ok(evaluateStaticPolicy(config, existingPaths.filter((x) => x !== 'privacy.html')).includes('REQUIRED_PUBLIC_FILE_MISSING:privacy.html'));
});
test('reject missing security policy file', () => {
  assert.ok(evaluateStaticPolicy(config, existingPaths.filter((x) => x !== 'security.html')).includes('REQUIRED_PUBLIC_FILE_MISSING:security.html'));
});
test('reject missing robots.txt', () => {
  assert.ok(evaluateStaticPolicy(config, existingPaths.filter((x) => x !== 'robots.txt')).includes('REQUIRED_PUBLIC_FILE_MISSING:robots.txt'));
});

test('the isolated static policy pilot does not introduce root build or dependency tooling', () => {
  assert.equal(existsSync(resolve(root, 'package.json')), false, 'root package.json can trigger a Vercel dependency install');
  assert.equal(existsSync(resolve(root, 'turbo.json')), false, 'Turborepo is outside the dependency-free static pilot');
});
