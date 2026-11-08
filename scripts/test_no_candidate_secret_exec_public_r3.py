"""PUBLIC R3 red/green: never execute candidate Python with private deny-hashes."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import safe_merge_evidence as evidence


class Recorder:
    def __init__(self):
        self.calls = []

    def run(self, args, **kwargs):
        self.calls.append((tuple(args), kwargs))
        return evidence.CommandResult(tuple(args), 0, "", "")


class CandidateVerifierSafetyTests(unittest.TestCase):
    def test_privacy_ok_refuses_untrusted_candidate_verifier_even_with_synthetic_deny_hash(self):
        runner = Recorder()
        subject = evidence.RealEvidence(ROOT, runner=runner)
        with mock.patch.dict(os.environ, {"RUMBO_PRIVACY_DENY_HASHES": "a"*64}), \
             mock.patch.object(evidence.verify_public_privacy, "commit_metadata_violations", return_value=[]):
            with self.assertRaisesRegex(evidence.EvidenceError, "untrusted|independent"):
                subject.privacy_ok("a"*40)
        self.assertEqual(runner.calls, [], "Untrusted candidate worktree/script must never execute")


if __name__ == "__main__":
    unittest.main()
