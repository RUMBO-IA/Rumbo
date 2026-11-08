"""PUBLIC R15: order workflow runs by actual instant, not timestamp characters.

Fixture-backed API only. No network/PR writes.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_public_r10_run_integrity import (
    LatestPrivacyEvidenceTests, PR, SHA, BRANCH, run
)
from safe_merge_evidence import EvidenceError


class ChronologicalRunOrderingTests(unittest.TestCase):
    def subject(self, entries, **kwargs):
        return LatestPrivacyEvidenceTests().subject(entries, **kwargs)

    def test_newest_actual_failure_with_utc_offset_is_not_hidden_by_older_success(self):
        # 12:00+02:00 == 10:00Z, older than 11:30Z.
        older_success=run(rid=123,date="2026-11-08T12:00:00+02:00")
        newer_failure=run(rid=124,date="2026-11-08T11:30:00Z",conclusion="failure")
        with self.assertRaisesRegex(EvidenceError,"newest.*not successful"):
            self.subject([older_success,newer_failure]).privacy_attestation(PR,SHA,"main",BRANCH)

    def test_newest_actual_success_is_not_displaced_by_older_offset_failure(self):
        older_failure=run(rid=122,date="2026-11-08T12:00:00+02:00",conclusion="failure")
        newest_success=run(rid=123,date="2026-11-08T11:30:00Z")
        receipt=self.subject([older_failure,newest_success]).privacy_attestation(PR,SHA,"main",BRANCH)
        self.assertEqual(receipt["run_id"],123)

    def test_postwrite_newer_failure_with_utc_offset_invalidates_old_receipt(self):
        old=run(rid=123,date="2026-11-08T12:00:00+02:00")
        new=run(rid=124,date="2026-11-08T11:30:00Z",conclusion="failure")
        obj=self.subject([old,new],post_run=old)
        previous={
            "run_id":123,"run_attempt":1,"pr_number":PR,
            "created_at":"2026-11-08T12:00:00+02:00",
            "independent_privacy_check":obj._require_independent_privacy_check(SHA),
        }
        with self.assertRaisesRegex(EvidenceError,"superseded|newer|invalid"):
            obj.privacy_attestation_by_run(previous,SHA,"main",BRANCH)

    def test_epoch_precedence_with_negative_timezone_offset(self):
        # 11:00-03:00 is 14:00Z, hence newer than 13:00Z.
        success=run(rid=123,date="2026-11-08T13:00:00Z")
        fail=run(rid=124,date="2026-11-08T11:00:00-03:00",conclusion="failure")
        with self.assertRaisesRegex(EvidenceError,"newest.*not successful"):
            self.subject([success,fail]).privacy_attestation(PR,SHA,"main",BRANCH)


if __name__=="__main__":
    unittest.main()
