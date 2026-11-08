"""Adversarial unit tests for PUBLIC historical ref evidence reconciliation.

Never alter refs; any changed/missing/unknown ref must fail closed.
"""
import unittest
from scripts.public_ref_contamination_audit import remote_ref,parse_ls_remote,reconcile
A="1"*40
B="2"*40
BAD="a"*40
NORMAL="refs/remotes/origin/recovery/branch"
PULL="refs/remotes/public-pr-head/369"
RN="refs/heads/recovery/branch"
RP="refs/pull/369/head"
def sample():
    expected={NORMAL:{BAD},PULL:{BAD}}
    local={NORMAL:A,PULL:B}
    remote={RN:A,RP:B}
    observed={NORMAL:{BAD},PULL:{BAD}}
    return expected,local,remote,observed

class PublicRefReconciliationTests(unittest.TestCase):
    def test_branch_ref_mapping(self):
        self.assertEqual(remote_ref(NORMAL),RN)
    def test_pr_virtual_head_mapping(self):
        self.assertEqual(remote_ref(PULL),RP)
    def test_pr_virtual_merge_mapping(self):
        self.assertEqual(remote_ref("refs/remotes/public-pr-merge/371"),"refs/pull/371/merge")
    def test_unmapped_ref_is_not_accepted(self):
        self.assertIsNone(remote_ref("refs/remotes/surprise/private"))
    def test_full_exact_evidence_remains_blocked(self):
        result=reconcile(*sample())
        self.assertEqual((result["classification"],result["verified_ref_count"]),("BLOCKED_EXTERNAL",2))
        self.assertFalse(result["merge_authorized"])
    def test_changed_tip_is_not_claimed_clean(self):
        e,l,r,o=sample()
        r[RN]="3"*40
        result=reconcile(e,l,r,o)
        self.assertEqual(result["classification"],"UNRESOLVED")
        self.assertFalse(result["merge_authorized"])
    def test_missing_virtual_ref_is_not_claimed_clean(self):
        e,l,r,o=sample()
        r.pop(RP)
        self.assertEqual(reconcile(e,l,r,o)["classification"],"UNRESOLVED")
    def test_changed_bad_commit_containment_is_not_claimed_clean(self):
        e,l,r,o=sample()
        o[NORMAL]=set()
        self.assertEqual(reconcile(e,l,r,o)["classification"],"UNRESOLVED")
    def test_duplicate_remote_ref_fails_closed(self):
        line=f"{A}\t{RN}\n"
        with self.assertRaises(ValueError):
            parse_ls_remote(line+line)
    def test_malformed_remote_sha_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_ls_remote(f"xyz\t{RN}\n")
    def test_empty_expected_evidence_not_proven(self):
        self.assertEqual(reconcile({}, {}, {}, {})["classification"],"UNRESOLVED")

if __name__=="__main__":
    unittest.main()
