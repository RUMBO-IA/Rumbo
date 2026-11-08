"""PUBLIC R6: required CI source and completeness, no network or changes.

These tests exercise the production RealEvidence interface using deterministic
GitHub response fixtures. They must fail on the unpatched R5 candidate.
"""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from safe_merge_evidence import RealEvidence, EvidenceError
from safe_merge_policy import DEFAULT_POLICY

SHA="3fee7db5677e50a7637f7e3f7abd5917001a56bd"
BAD_SHA="0"*40


def check(name="privacy",app_id=15368,sha=SHA,conclusion="success",run_id=123):
    return {"id":run_id,"name":name,"head_sha":sha,"status":"completed",
            "conclusion":conclusion,"app":{"id":app_id}}


class RequiredCheckProvenanceTests(unittest.TestCase):
    def subject(self,runs=None,total=None,statuses=None):
        result={"total_count":len(runs or []) if total is None else total,
                "check_runs":list(runs or [])}
        status={"statuses":list(statuses or [])}
        obj=RealEvidence(ROOT,runner=object())
        obj._json=lambda args: result if "/check-runs" in str(args[-1]) else status
        return obj

    def test_complete_authorized_check_runs_are_successful(self):
        obj=self.subject([check(),check(name="Vercel",app_id=8329,run_id=124)])
        states=obj.checks(SHA)
        self.assertEqual((states["privacy"],states["Vercel"]),("SUCCESS","SUCCESS"))

    def test_truncated_check_run_listing_must_fail_closed(self):
        obj=self.subject([check()],total=32)
        with self.assertRaisesRegex(EvidenceError,"incomplete|truncat|total_count"):
            obj.checks(SHA)

    def test_check_run_missing_total_count_must_fail_closed(self):
        obj=self.subject([check()])
        original=obj._json
        def incomplete(args):
            d=original(args)
            return {"check_runs":d["check_runs"]} if "check_runs" in d else d
        obj._json=incomplete
        with self.assertRaisesRegex(EvidenceError,"incomplete|total_count"):
            obj.checks(SHA)

    def test_check_run_on_different_head_is_not_successful(self):
        obj=self.subject([check(sha=BAD_SHA)])
        self.assertNotEqual(obj.checks(SHA).get("privacy"),"SUCCESS")

    def test_wrong_app_cannot_satisfy_privacy_context(self):
        obj=self.subject([check(app_id=999999)])
        self.assertNotEqual(obj.checks(SHA).get("privacy"),"SUCCESS")

    def test_unverified_status_only_vercel_cannot_satisfy_pinned_context(self):
        obj=self.subject(statuses=[{"context":"Vercel","state":"success"}])
        self.assertNotEqual(obj.checks(SHA).get("Vercel"),"SUCCESS")

    def test_failed_authorized_run_overrides_successful_duplicate(self):
        obj=self.subject([check(),check(conclusion="failure",run_id=124)])
        self.assertEqual(obj.checks(SHA)["privacy"],"FAILURE")


def protection(app_privacy=15368,app_vercel=8329,strict=True,include_app=True):
    checks=([{"context":"privacy","app_id":app_privacy},
             {"context":"Vercel","app_id":app_vercel}] if include_app else [])
    return {
        "required_status_checks":{"strict":strict,"contexts":["privacy","Vercel"],"checks":checks},
        "enforce_admins":{"enabled":True},
        "required_linear_history":{"enabled":True},
        "allow_force_pushes":{"enabled":False},
        "required_conversation_resolution":{"enabled":True},
    }


class RequiredProtectionProvenanceTests(unittest.TestCase):
    def verify(self,blob):
        obj=RealEvidence(ROOT,runner=object())
        obj._json=lambda args:blob
        return obj.branch_protection_ok("main",("privacy","Vercel"))

    def test_live_pinned_apps_are_accepted(self):
        self.assertTrue(self.verify(protection()))

    def test_renamed_or_wrong_app_is_rejected(self):
        self.assertFalse(self.verify(protection(app_privacy=999999)))

    def test_missing_source_app_pins_are_rejected(self):
        self.assertFalse(self.verify(protection(include_app=False)))

    def test_non_strict_required_checks_are_rejected(self):
        self.assertFalse(self.verify(protection(strict=False)))


if __name__=="__main__":
    unittest.main()
