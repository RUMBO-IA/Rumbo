"""PUBLIC R14 TDD: no merge write if required evidence changes before fast_forward.

Uses fake GitHub/checks and fake push recorder; never contacts external services.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import safe_merge_authority as authority
import safe_merge_policy as policy
from test_safe_merge_authority import FakeEvidence, merge_request, BASE, HEAD

GOOD={"privacy":"SUCCESS","Vercel":"SUCCESS"}

class ChangingEvidence(FakeEvidence):
    def __init__(self, checks_sequence, **kwargs):
        super().__init__(target_sequence=[BASE, BASE, HEAD], **kwargs)
        self.sequence=list(checks_sequence)
        self.check_reads=0
    def checks(self,sha):
        self.check_reads+=1
        return dict(self.sequence[min(self.check_reads-1,len(self.sequence)-1)])

class PreWriteRecheckTests(unittest.TestCase):
    def test_vercel_fails_after_preflight_blocks_before_push(self):
        ev=ChangingEvidence([GOOD,{"privacy":"SUCCESS","Vercel":"FAILURE"}])
        result=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="main")
        self.assertEqual((result.state,result.failed_gate),("SAFE_STOP","REQUIRED_CHECKS_RECHECK"))
        self.assertEqual(result.gates[-1].evidence["checks"]["Vercel"],"FAILURE")
        self.assertEqual(ev.push_calls,[])
        self.assertGreaterEqual(ev.check_reads,2)

    def test_privacy_becomes_pending_before_write_blocks_without_push(self):
        ev=ChangingEvidence([GOOD,{"privacy":"PENDING","Vercel":"SUCCESS"}])
        result=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="main")
        self.assertEqual((result.state,result.failed_gate),("SAFE_STOP","REQUIRED_CHECKS_RECHECK"))
        self.assertEqual(ev.push_calls,[])

    def test_status_becomes_source_unproven_before_write_blocks(self):
        ev=ChangingEvidence([GOOD,{"privacy":"SUCCESS","Vercel":"UNPROVEN_SOURCE"}])
        result=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="main")
        self.assertEqual((result.state,result.failed_gate),("SAFE_STOP","REQUIRED_CHECKS_RECHECK"))
        self.assertFalse(ev.push_calls)

    def test_independent_privacy_receipt_revoked_before_write_blocks(self):
        ev=ChangingEvidence([GOOD, GOOD],post_attestation_sequence=[False,True])
        result=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="main")
        self.assertEqual((result.state,result.failed_gate),("SAFE_STOP","PRIVACY_ATTESTATION_RECHECK"))
        self.assertFalse(ev.push_calls)

    def test_stable_checks_and_private_receipt_allow_fake_push(self):
        ev=ChangingEvidence([GOOD,GOOD,GOOD])
        result=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="main")
        self.assertEqual(result.state,"MERGED_SAFE")
        self.assertEqual(ev.push_calls,[("main",BASE,HEAD)])
        self.assertGreaterEqual(ev.check_reads,3)
        self.assertGreaterEqual(ev.post_attestation_calls,2)

    def test_dry_run_never_pushes_even_with_successful_checks(self):
        ev=ChangingEvidence([GOOD])
        result=authority.evaluate(merge_request(),policy.DEFAULT_POLICY,ev,mode="dry-run")
        self.assertEqual(result.state,"DRY_RUN_PASS")
        self.assertFalse(ev.push_calls)

if __name__=="__main__":unittest.main()
