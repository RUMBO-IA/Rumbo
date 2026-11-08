"""PUBLIC R9: actionable required-check diagnosis must not authorize merge.

All mutation paths are mocked; RED/GREEN proof for the existing merge gate.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_safe_merge_authority import FakeEvidence, merge_request, policy, authority


class DiagnosticEvidence(FakeEvidence):
    def __init__(self, *, blocked=True, raise_diagnostic=False, **kwargs):
        super().__init__(**kwargs)
        self.blocked = blocked
        self.raise_diagnostic = raise_diagnostic
        self.diagnostic_calls = []

    def vercel_required_check_diagnostics(self, sha, branch, required):
        self.diagnostic_calls.append((sha,branch,required))
        if self.raise_diagnostic:
            raise RuntimeError("diagnostic read-only query unavailable")
        return {
            "classification": "BLOCKED_POLICY" if self.blocked else "REQUIRES_LIVE_CHECK_EVIDENCE",
            "automatic_deployment_enabled": not self.blocked,
            "policy_conflict": self.blocked,
            "merge_authorized": False,
        }


class PublicR9CheckGateTests(unittest.TestCase):
    def test_vercel_missing_has_policy_root_cause_without_bypass(self):
        ev=DiagnosticEvidence(checks={"privacy":"SUCCESS","Vercel":"MISSING"})
        out=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="main")
        self.assertEqual((out.state,out.failed_gate),("SAFE_STOP","REQUIRED_CHECKS"))
        self.assertEqual(out.gates[-1].evidence["vercel_policy"]["classification"],"BLOCKED_POLICY")
        self.assertEqual(out.gates[-1].evidence["checks"]["Vercel"],"MISSING")
        self.assertEqual(len(ev.diagnostic_calls),1)
        self.assertFalse(ev.push_calls)

    def test_diagnostic_never_converts_missing_required_check_into_success(self):
        ev=DiagnosticEvidence(blocked=False,checks={"privacy":"SUCCESS","Vercel":"MISSING"})
        out=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="main")
        self.assertEqual((out.state,out.failed_gate),("SAFE_STOP","REQUIRED_CHECKS"))
        self.assertFalse(ev.push_calls)

    def test_privacy_only_failure_skips_vercel_diagnostics(self):
        ev=DiagnosticEvidence(checks={"privacy":"FAILURE","Vercel":"SUCCESS"})
        out=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="main")
        self.assertEqual((out.state,out.failed_gate),("SAFE_STOP","REQUIRED_CHECKS"))
        self.assertEqual(ev.diagnostic_calls,[])
        self.assertFalse(ev.push_calls)

    def test_diagnostic_failure_is_not_merge_authority(self):
        ev=DiagnosticEvidence(checks={"privacy":"SUCCESS","Vercel":"MISSING"},raise_diagnostic=True)
        out=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="main")
        self.assertEqual((out.state,out.failed_gate),("SAFE_STOP","REQUIRED_CHECKS"))
        self.assertEqual(out.gates[-1].evidence["vercel_policy"]["classification"],"NOT_PROVEN")
        self.assertFalse(ev.push_calls)

    def test_when_all_checks_successful_diagnostic_not_called(self):
        ev=DiagnosticEvidence()
        out=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="dry-run")
        self.assertEqual(out.state,"DRY_RUN_PASS")
        self.assertEqual(ev.diagnostic_calls,[])
        self.assertFalse(ev.push_calls)


if __name__=="__main__":
    unittest.main()
