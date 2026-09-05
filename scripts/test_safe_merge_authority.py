import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import safe_merge_policy as policy
import safe_merge_evidence as evidence
import safe_merge_authority as authority
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


BASE = "1" * 40
HEAD = "2" * 40


def merge_request(head=HEAD, base="main", repository="RUMBO-IA/Rumbo"):
    return policy.MergeRequest(40, head, base, repository)


class FakeEvidence:
    def __init__(self, *, head=HEAD, base="main", repo="RUMBO-IA/Rumbo", checks=None,
                 privacy=True, ancestor=True, vercel=None, target_sequence=None, ruleset=True):
        self.head, self.base, self.repo = head, base, repo
        self.check_states = checks if checks is not None else {"privacy": "SUCCESS", "Vercel": "SUCCESS"}
        self.privacy, self.ancestor, self.ruleset = privacy, ancestor, ruleset
        self.vercel = vercel or {"autoAssignCustomDomains": False, "commandForIgnoringBuildStep": None,
                                 "productionBranch": "main", "liveDeployment": "dpl_live", "liveTarget": "production"}
        self.targets = list(target_sequence or [BASE, BASE, HEAD])
        self.push_calls = []

    def pr(self, _number):
        return {"state": "OPEN", "base": self.base, "head": self.head, "repo": self.repo, "cross": False}

    def checks(self, _sha): return dict(self.check_states)
    def target_sha(self, _target): return self.targets.pop(0) if len(self.targets) > 1 else self.targets[0]
    def is_ancestor(self, _base, _candidate): return self.ancestor
    def privacy_ok(self, _candidate): return self.privacy
    def vercel_state(self): return dict(self.vercel)
    def ruleset_ok(self): return self.ruleset
    def fast_forward(self, target, expected_old, candidate):
        self.push_calls.append((target, expected_old, candidate))
        return evidence.CommandResult(("git", "push"), 0, "", "")


class AuthorityGateTests(unittest.TestCase):
    def test_stale_head_stops_at_g1(self):
        out = authority.evaluate(merge_request(head="a" * 40), policy.DEFAULT_POLICY, FakeEvidence(head="b" * 40))
        self.assertEqual((out.state, out.failed_gate), ("SAFE_STOP", "PR_IDENTITY"))

    def test_wrong_repository_stops_at_g1(self):
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, FakeEvidence(repo="other/repo"))
        self.assertEqual(out.failed_gate, "PR_IDENTITY")

    def test_missing_required_check_stops_at_g2(self):
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, FakeEvidence(checks={"privacy": "SUCCESS"}))
        self.assertEqual(out.failed_gate, "REQUIRED_CHECKS")

    def test_privacy_violation_stops_at_g3(self):
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, FakeEvidence(privacy=False))
        self.assertEqual(out.failed_gate, "PRIVACY_ANCESTRY")

    def test_non_descendant_stops_at_g3(self):
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, FakeEvidence(ancestor=False))
        self.assertEqual(out.failed_gate, "PRIVACY_ANCESTRY")
    def test_vercel_drift_stops_at_g4(self):
        bad = {
            "autoAssignCustomDomains": True,
            "commandForIgnoringBuildStep": None,
            "productionBranch": "main",
            "liveDeployment": "dpl_live",
            "liveTarget": "production",
        }
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, FakeEvidence(vercel=bad))
        self.assertEqual(out.failed_gate, "PRODUCTION_NO_GO")

    def test_target_tip_drift_stops_at_g5(self):
        ev = FakeEvidence(target_sequence=[BASE, "3" * 40])
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev)
        self.assertEqual(out.failed_gate, "FAST_FORWARD_ONLY")
        self.assertFalse(ev.push_calls)

    def test_clean_dry_run_passes_without_write(self):
        ev = FakeEvidence(target_sequence=[BASE, BASE])
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev)
        self.assertEqual(out.state, "DRY_RUN_PASS")
        self.assertIsNone(out.failed_gate)
        self.assertFalse(ev.push_calls)
