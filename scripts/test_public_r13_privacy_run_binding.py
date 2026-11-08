"""R13 PUBLIC: latest exact-head privacy run cannot be hidden by missing PR binding.

All GitHub API responses are fixture data. No network or changes.
"""
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_public_r10_run_integrity import (
    LatestPrivacyEvidenceTests, PR, SHA, BRANCH, run,
)
from safe_merge_evidence import EvidenceError


class LatestRunAssociationBoundaryTests(unittest.TestCase):
    def subject(self, entries):
        return LatestPrivacyEvidenceTests().subject(entries)

    def test_newest_run_missing_pr_association_must_not_hide_failure(self):
        older = run()
        newer = run(rid=124, date="2026-11-08T06:00:00Z",
                    conclusion="failure", prs=[])
        obj = self.subject([newer, older])
        with self.assertRaisesRegex(EvidenceError, "newest|association|bound|ambiguous"):
            obj.privacy_attestation(PR, SHA, "main", BRANCH)

    def test_newest_run_associated_to_different_pr_cannot_be_ignored(self):
        older = run()
        newer = run(rid=124, date="2026-11-08T06:00:00Z",
                    conclusion="failure", prs=[{"number": 1111}])
        obj = self.subject([older, newer])
        with self.assertRaisesRegex(EvidenceError, "newest|association|bound|ambiguous"):
            obj.privacy_attestation(PR, SHA, "main", BRANCH)

    def test_newer_successful_bound_run_is_valid_even_with_older_unbound(self):
        older = run(rid=122, date="2026-11-08T04:00:00Z", prs=[])
        latest = run(rid=123, date="2026-11-08T06:00:00Z")
        obj = self.subject([latest, older])
        receipt = obj.privacy_attestation(PR, SHA, "main", BRANCH)
        self.assertEqual(receipt["run_id"], 123)

    def test_failed_unrelated_branch_does_not_supersede_exact_branch(self):
        current = run()
        unrelated = run(rid=124, date="2026-11-08T06:00:00Z",
                        conclusion="failure", branch="another-branch", prs=[])
        obj = self.subject([current, unrelated])
        receipt = obj.privacy_attestation(PR, SHA, "main", BRANCH)
        self.assertEqual(receipt["run_id"], 123)

    def test_latest_run_with_malformed_id_fails_closed(self):
        bad = run(rid="not-an-integer", date="2026-11-08T06:00:00Z")
        obj = self.subject([run(), bad])
        with self.assertRaisesRegex(EvidenceError, "run id|run metadata|malformed"):
            obj.privacy_attestation(PR, SHA, "main", BRANCH)

    def test_latest_run_with_invalid_attempt_fails_closed(self):
        bad = run(rid=125, attempt="bad", date="2026-11-08T06:00:00Z")
        obj = self.subject([run(), bad])
        with self.assertRaisesRegex(EvidenceError, "attempt|run metadata|malformed"):
            obj.privacy_attestation(PR, SHA, "main", BRANCH)

    def test_latest_run_missing_created_at_fails_closed(self):
        bad = run(rid=125)
        bad.pop("created_at")
        obj = self.subject([bad])
        with self.assertRaisesRegex(EvidenceError, "created_at|run metadata|malformed"):
            obj.privacy_attestation(PR, SHA, "main", BRANCH)


    def test_postwrite_newer_run_missing_timestamp_cannot_hide_invalid_receipt(self):
        original = run()
        newer = run(rid=124, conclusion="failure")
        newer.pop("created_at")
        obj = self.subject([original, newer])
        receipt = {"run_id": 123, "run_attempt": 1,
                   "created_at": "2026-11-08T05:00:00Z", "pr_number": PR,
                   "independent_privacy_check": obj._require_independent_privacy_check(SHA)}
        with self.assertRaisesRegex(EvidenceError, "created_at|run metadata|malformed"):
            obj.privacy_attestation_by_run(receipt, SHA, "main", BRANCH)

    def test_postwrite_newer_run_invalid_attempt_cannot_hide_invalid_receipt(self):
        original = run()
        newer = run(rid=124, conclusion="failure", attempt="bad",
                    date="2026-11-08T06:00:00Z")
        obj = self.subject([original, newer])
        receipt = {"run_id": 123, "run_attempt": 1,
                   "created_at": "2026-11-08T05:00:00Z", "pr_number": PR,
                   "independent_privacy_check": obj._require_independent_privacy_check(SHA)}
        with self.assertRaisesRegex(EvidenceError, "attempt|run metadata|malformed"):
            obj.privacy_attestation_by_run(receipt, SHA, "main", BRANCH)


if __name__ == "__main__":
    unittest.main()
