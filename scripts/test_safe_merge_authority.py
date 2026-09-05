import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import safe_merge_policy as policy


class PolicyTests(unittest.TestCase):
    def test_main_request_is_allowed(self):
        request = policy.MergeRequest(40, "a" * 40, "main", "RUMBO-IA/Rumbo")
        policy.validate_request(request, policy.DEFAULT_POLICY)
        policy.validate_execution_mode("main", request.expected_base, policy.DEFAULT_POLICY)

    def test_non_main_target_is_rejected(self):
        with self.assertRaises(policy.PolicyError):
            policy.validate_execution_mode("main", "release", policy.DEFAULT_POLICY)

    def test_probe_prefix_is_required(self):
        policy.validate_execution_mode("probe", "probe/safe-merge-case", policy.DEFAULT_POLICY)
        with self.assertRaises(policy.PolicyError):
            policy.validate_execution_mode("probe", "probe/other", policy.DEFAULT_POLICY)
