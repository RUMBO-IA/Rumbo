import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import safe_merge_policy as policy
import safe_merge_evidence as evidence
import safe_merge_receipt as receipt


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


class ReceiptTests(unittest.TestCase):
    def test_digest_is_order_independent(self):
        self.assertEqual(
            receipt.receipt_digest({"b": 2, "a": 1}),
            receipt.receipt_digest({"a": 1, "b": 2}),
        )

    def test_receipt_is_content_addressed_and_immutable(self):
        with tempfile.TemporaryDirectory() as td:
            payload = {"state": "SAFE_STOP"}
            path = receipt.write_receipt(Path(td), payload)
            self.assertEqual(path.stem, receipt.receipt_digest(payload))
            stored = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(stored["sha256"], path.stem)
            self.assertEqual(stored["payload"], payload)
            with self.assertRaises(FileExistsError):
                receipt.write_receipt(Path(td), payload)


class FakeRunner:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def run(self, args, **_kwargs):
        args = tuple(args)
        self.calls.append(args)
        for prefix, result in self.responses.items():
            if args[:len(prefix)] == prefix:
                if isinstance(result, evidence.CommandResult):
                    return result
                return evidence.CommandResult(args, 0, result, "")
        return evidence.CommandResult(args, 1, "", "unexpected command")


class EvidenceTests(unittest.TestCase):
    def test_pr_snapshot_normalizes_exact_fields(self):
        payload = '{"number":40,"state":"OPEN","baseRefName":"main","headRefOid":"' + "a" * 40 + '","headRepository":{"nameWithOwner":"RUMBO-IA/Rumbo"},"isCrossRepository":false,"statusCheckRollup":[]}'
        fake = FakeRunner({("gh", "pr", "view"): payload})
        ev = evidence.RealEvidence(ROOT, fake, policy.DEFAULT_POLICY)
        snapshot = ev.pr(40)
        self.assertEqual(snapshot["base"], "main")
        self.assertEqual(snapshot["repo"], "RUMBO-IA/Rumbo")
        self.assertIn("--json", fake.calls[0])

    def test_nonzero_command_fails_closed(self):
        result = evidence.CommandResult(("gh",), 1, "", "boom")
        with self.assertRaises(evidence.EvidenceError):
            evidence.parse_json_result(result)

    def test_vercel_state_normalizes_project_and_live_alias(self):
        project = '{"autoAssignCustomDomains":false,"commandForIgnoringBuildStep":null,"link":{"productionBranch":"main"}}'
        live = '{"id":"dpl_live","target":"production"}'
        fake = FakeRunner({("vercel", "api"): project, ("vercel", "inspect"): live})
        state = evidence.RealEvidence(ROOT, fake, policy.DEFAULT_POLICY).vercel_state()
        self.assertEqual(state["liveDeployment"], "dpl_live")
        self.assertFalse(state["autoAssignCustomDomains"])
        self.assertIsNone(state["commandForIgnoringBuildStep"])
        self.assertEqual(state["productionBranch"], "main")
