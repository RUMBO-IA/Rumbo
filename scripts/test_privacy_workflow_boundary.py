"""Conservative YAML contract check; not an independent private PR attestation."""
import unittest
from pathlib import Path
import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / '.github/workflows/privacy-gate.yml'
GUARD = "github.event_name == 'push' && github.ref == 'refs/heads/main'"
SECRET = 'secrets.RUMBO_PRIVACY_DENY_HASHES'
STEP = 'Verify public privacy invariants (trusted main only)'


class UniqueLoader(yaml.BaseLoader):
    """String scalars preserve Actions' `on` key; no Python object construction."""
    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key == '<<' or key in result:
                raise ValueError('duplicate or unsupported YAML key')
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def values(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from values(item)
    elif isinstance(value, list):
        for item in value:
            yield from values(item)
    elif isinstance(value, str):
        yield value


def validate(workflow: str) -> list[str]:
    try:
        # Unsupported indirection fails closed; never resolve custom tags or aliases.
        if any(isinstance(t, (yaml.tokens.AnchorToken, yaml.tokens.AliasToken,
                              yaml.tokens.TagToken)) for t in yaml.scan(workflow)):
            return ['UNSUPPORTED_YAML_INDIRECTION']
        doc = yaml.load(workflow, Loader=UniqueLoader)
    except (yaml.YAMLError, ValueError, TypeError, RecursionError):
        return ['INVALID_OR_DUPLICATE_YAML']
    if not isinstance(doc, dict):
        return ['INVALID_WORKFLOW_STRUCTURE']
    errors = []
    events = doc.get('on', {})
    if not isinstance(events, dict):
        return ['INVALID_EVENT_MAPPING']
    if 'pull_request_target' in events:
        errors.append('PRIVILEGED_PR_EVENT')
    if 'workflow_run' in events:
        errors.append('PRIVILEGED_CHAIN_EVENT')
    if 'pull_request' not in events:
        errors.append('MISSING_PUBLIC_PR_TRIGGER')
    if set(events) != {'push', 'pull_request'}:
        errors.append('UNEXPECTED_WORKFLOW_TRIGGER')
    if sum(v.count(SECRET) for v in values(doc)) != 1:
        errors.append('PRIVATE_SECRET_REFERENCE_COUNT')
    jobs = doc.get('jobs')
    if not isinstance(jobs, dict) or set(jobs) != {'privacy'}:
        errors.append('UNEXPECTED_JOB_SET')
    allowed_secret = '${{ ' + SECRET + ' }}'
    if any(isinstance(v, str) and 'secrets.' in v.lower() and v != allowed_secret
           for v in values(doc)):
        errors.append('UNAUTHORIZED_SECRET_REFERENCE')
    job = jobs.get('privacy') if isinstance(jobs, dict) else None
    steps = job.get('steps') if isinstance(job, dict) else None
    if not isinstance(steps, list) or not all(isinstance(s, dict) for s in steps):
        return errors + ['INVALID_JOB_STRUCTURE']
    matches = [s for s in steps if s.get('name') == STEP]
    if len(matches) != 1:
        errors.append('MISSING_OR_DUPLICATE_TRUSTED_MAIN_STEP')
    else:
        step = matches[0]
        if step.get('if') not in (GUARD, '${{ ' + GUARD + ' }}'):
            errors.append('MISSING_MAIN_PUSH_GUARD')
        env = step.get('env')
        if not isinstance(env, dict) or env.get('RUMBO_PRIVACY_DENY_HASHES') != '${{ ' + SECRET + ' }}':
            errors.append('SECRET_OUTSIDE_MAIN_STEP')
        if not isinstance(env, dict) or env.get('RUMBO_PRIVACY_COMMIT_SHA') != '${{ github.sha }}':
            errors.append('MISSING_EXACT_PUSH_SHA')
        if step.get('run') != 'python scripts/verify_public_privacy.py':
            errors.append('MISSING_PRIVATE_VERIFIER')
        if 'uses' in step or 'continue-on-error' in step:
            errors.append('UNSUPPORTED_PRIVATE_STEP_OVERRIDE')
    if doc.get('permissions') != {'contents': 'read'} or (isinstance(job, dict) and 'permissions' in job):
        errors.append('MISSING_READONLY_TOKEN')
    return errors


class PrivacyWorkflowBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.source = WORKFLOW.read_text(encoding='utf-8')

    def change_guard(self, replacement):
        old = 'if: ${{ ' + GUARD + ' }}'
        self.assertEqual(self.source.count(old), 1)
        return self.source.replace(old, replacement)

    def test_current_workflow(self):
        self.assertEqual(validate(self.source), [])

    def test_comment_cannot_authorize_always(self):
        self.assertIn('MISSING_MAIN_PUSH_GUARD', validate(self.change_guard('if: ${{ always() }}\n        # ' + GUARD)))

    def test_guard_only_in_comment_is_rejected(self):
        self.assertIn('MISSING_MAIN_PUSH_GUARD', validate(self.change_guard('# if: ${{ ' + GUARD + ' }}')))

    def test_guard_prefix_with_or_true_is_rejected(self):
        self.assertIn('MISSING_MAIN_PUSH_GUARD', validate(self.change_guard('if: ${{ ' + GUARD + ' || true }}')))

    def test_duplicate_if_is_rejected(self):
        self.assertIn('INVALID_OR_DUPLICATE_YAML', validate(self.change_guard('if: ${{ ' + GUARD + ' }}\n        if: ${{ always() }}')))

    def test_duplicate_top_level_permissions_is_rejected(self):
        self.assertIn('INVALID_OR_DUPLICATE_YAML', validate(self.source + '\npermissions: write-all\n'))

    def test_quoted_duplicate_key_is_rejected(self):
        self.assertIn('INVALID_OR_DUPLICATE_YAML', validate(self.source + '\n"permissions": write-all\n'))

    def test_privileged_event_is_rejected(self):
        self.assertIn('PRIVILEGED_PR_EVENT', validate(self.source.replace('on:\n', 'on:\n  pull_request_target:\n', 1)))

    def test_privileged_chain_is_rejected(self):
        self.assertIn('PRIVILEGED_CHAIN_EVENT', validate(self.source.replace('on:\n', 'on:\n  workflow_run:\n', 1)))

    def test_guard_in_run_block_is_rejected(self):
        self.assertIn('MISSING_MAIN_PUSH_GUARD', validate(self.change_guard('if: true\n        description: |\n          if: ${{ ' + GUARD + ' }}')))

    def test_extra_secret_reference_is_rejected(self):
        changed = self.source.replace('env:\n', 'env:\n          EXTRA: ${{ ' + SECRET + ' }}\n', 1)
        self.assertIn('PRIVATE_SECRET_REFERENCE_COUNT', validate(changed))

    def test_secret_only_in_comment_is_rejected(self):
        changed = self.source.replace('          RUMBO_PRIVACY_DENY_HASHES:', '          # RUMBO_PRIVACY_DENY_HASHES:')
        self.assertIn('SECRET_OUTSIDE_MAIN_STEP', validate(changed))

    def test_write_permission_is_rejected(self):
        self.assertIn('MISSING_READONLY_TOKEN', validate(self.source.replace('contents: read', 'contents: write')))

    def test_job_permission_override_is_rejected(self):
        changed = self.source.replace('  privacy:\n', '  privacy:\n    permissions: write-all\n')
        self.assertIn('MISSING_READONLY_TOKEN', validate(changed))

    def test_unexpected_job_is_rejected(self):
        original = '  privacy:' + chr(10)
        injected = (
            '  extra:' + chr(10)
            + '    runs-on: ubuntu-latest' + chr(10)
            + '    permissions:' + chr(10)
            + '      contents: write' + chr(10)
            + '    steps:' + chr(10)
            + '      - run: echo harmless' + chr(10)
            + original
        )
        self.assertEqual(self.source.count(original), 1)
        changed = self.source.replace(original, injected, 1)
        self.assertIn('UNEXPECTED_JOB_SET', validate(changed))

    def test_other_secret_is_rejected(self):
        changed = self.source.replace(
            "          RUMBO_PRIVACY_SCAN_ALL_REFS: '1'",
            "          RUMBO_PRIVACY_SCAN_ALL_REFS: '1'\n          EXTRA: ${{ secrets.OTHER_CREDENTIAL }}"
        )
        self.assertIn('UNAUTHORIZED_SECRET_REFERENCE', validate(changed))

    def test_workflow_dispatch_is_rejected(self):
        changed = self.source.replace('on:\n', 'on:\n  workflow_dispatch:\n', 1)
        self.assertIn('UNEXPECTED_WORKFLOW_TRIGGER', validate(changed))

    def test_schedule_is_rejected(self):
        changed = self.source.replace('on:\n', "on:\n  schedule:\n    - cron: '0 1 * * *'\n", 1)
        self.assertIn('UNEXPECTED_WORKFLOW_TRIGGER', validate(changed))

    def test_custom_tag_is_rejected(self):
        self.assertIn('UNSUPPORTED_YAML_INDIRECTION', validate('x: !!python/object:example {}'))

    def test_yaml_anchor_is_rejected(self):
        self.assertIn('UNSUPPORTED_YAML_INDIRECTION', validate(self.source + '\nx: &guard true\ny: *guard\n'))

    def test_invalid_yaml_is_rejected(self):
        self.assertIn('INVALID_OR_DUPLICATE_YAML', validate('jobs: [unterminated'))

    def test_yaml_on_key_is_not_boolean(self):
        self.assertEqual(validate(self.source.replace('on:\n', '"on":\n', 1)), [])

    def test_wrong_commit_binding_is_rejected(self):
        changed = self.source.replace('RUMBO_PRIVACY_COMMIT_SHA: ${{ github.sha }}', 'RUMBO_PRIVACY_COMMIT_SHA: main')
        self.assertIn('MISSING_EXACT_PUSH_SHA', validate(changed))

    def test_ignored_failure_is_rejected(self):
        changed = self.change_guard('continue-on-error: true\n        if: ${{ ' + GUARD + ' }}')
        self.assertIn('UNSUPPORTED_PRIVATE_STEP_OVERRIDE', validate(changed))


if __name__ == '__main__':
    unittest.main()
