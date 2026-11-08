"""Adversarial PUBLIC R3 privacy receipt tests (no secrets, no network).

Synthetic app IDs here are fixtures. DEFAULT_POLICY has no approved app.
"""
from dataclasses import replace
import sys
import unittest
from pathlib import Path
import scripts.test_private_step_receipt_public_r2 as r2
sys.path.insert(0, str(Path(__file__).resolve().parent))
import safe_merge_evidence as evidence

TRUSTED_APP = 777777
CHECK_ID = 42424242


class ProtectedPrivacyReceiptTests(unittest.TestCase):
    def subject(self, *, private_step="skipped", returned_app=TRUSTED_APP,
                returned_sha=r2.HEAD, duplicate=False, total=None,
                conclusion="success", completed_at="2026-11-08T05:00:00Z",
                checked_name=None):
        obj = r2.PrivateStepReceiptTests().subject(conclusion=private_step)
        obj.policy = replace(obj.policy, independent_privacy_app_id=TRUSTED_APP)
        prior_query = obj._json

        def query(args):
            ep = next((str(x) for x in args
                       if str(x).startswith("repos/RUMBO-IA/Rumbo/")), "")
            if "/commits/" in ep and "/check-runs" in ep:
                checks = [{
                    "id": CHECK_ID,
                    "name": checked_name or obj.policy.independent_privacy_check_name,
                    "head_sha": returned_sha,
                    "status": "completed", "conclusion": conclusion,
                    "completed_at": completed_at, "app": {"id": returned_app}
                }]
                if duplicate:
                    checks.append(dict(checks[0], id=CHECK_ID + 1))
                return {"total_count": len(checks) if total is None else total,
                        "check_runs": checks}
            return prior_query(args)

        obj._json = query
        return obj

    def test_green_legacy_pr_secret_step_does_not_grant_private_authority(self):
        obj = r2.PrivateStepReceiptTests().subject(conclusion="success")
        with self.assertRaisesRegex(evidence.EvidenceError, "independent|trusted"):
            obj.privacy_attestation(374, r2.HEAD, "main", r2.BRANCH)

    def test_configured_independent_app_accepts_skipped_public_private_step(self):
        obj = self.subject(private_step="skipped")
        receipt = obj.privacy_attestation(374, r2.HEAD, "main", r2.BRANCH)
        self.assertEqual(receipt["independent_privacy_check"]["id"], CHECK_ID)
        self.assertEqual(receipt["independent_privacy_check"]["app_id"], TRUSTED_APP)

    def test_wrong_app_is_not_authority(self):
        obj = self.subject(returned_app=888888)
        with self.assertRaisesRegex(evidence.EvidenceError, "independent"):
            obj.privacy_attestation(374, r2.HEAD, "main", r2.BRANCH)

    def test_successful_other_commit_is_not_authority(self):
        obj = self.subject(returned_sha="0" * 40)
        with self.assertRaisesRegex(evidence.EvidenceError, "exact HEAD"):
            obj.privacy_attestation(374, r2.HEAD, "main", r2.BRANCH)

    def test_duplicate_matching_checks_are_rejected(self):
        obj = self.subject(duplicate=True)
        with self.assertRaisesRegex(evidence.EvidenceError, "ambiguous"):
            obj.privacy_attestation(374, r2.HEAD, "main", r2.BRANCH)

    def test_truncated_api_page_is_rejected(self):
        obj = self.subject(total=100)
        with self.assertRaisesRegex(evidence.EvidenceError, "incomplete"):
            obj.privacy_attestation(374, r2.HEAD, "main", r2.BRANCH)

    def test_failed_independent_check_is_rejected(self):
        obj = self.subject(conclusion="failure")
        with self.assertRaisesRegex(evidence.EvidenceError, "successful"):
            obj.privacy_attestation(374, r2.HEAD, "main", r2.BRANCH)

    def test_absent_independent_check_name_is_rejected(self):
        obj = self.subject(checked_name="untrusted-privacy")
        with self.assertRaisesRegex(evidence.EvidenceError, "missing"):
            obj.privacy_attestation(374, r2.HEAD, "main", r2.BRANCH)

    def test_post_write_unchanged_independent_receipt_passes(self):
        obj = self.subject()
        previous = obj.privacy_attestation(374, r2.HEAD, "main", r2.BRANCH)
        later = obj.privacy_attestation_by_run(previous, r2.HEAD, "main", r2.BRANCH)
        self.assertEqual(later["independent_privacy_check"], previous["independent_privacy_check"])

    def test_post_write_independent_receipt_change_rejected(self):
        obj = self.subject()
        previous = obj.privacy_attestation(374, r2.HEAD, "main", r2.BRANCH)
        orig = obj._json
        def swapped(args):
            data = orig(args)
            if isinstance(data, dict) and "check_runs" in data:
                data["check_runs"][0]["id"] = CHECK_ID + 1
            return data
        obj._json = swapped
        with self.assertRaisesRegex(evidence.EvidenceError, "changed after write"):
            obj.privacy_attestation_by_run(previous, r2.HEAD, "main", r2.BRANCH)


if __name__ == "__main__":
    unittest.main()
