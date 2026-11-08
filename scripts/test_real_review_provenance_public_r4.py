"""No-network provenance tests of the exact-HEAD independent review reader."""
import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from safe_merge_evidence import RealEvidence, EvidenceError

HEAD="3fee7db5677e50a7637f7e3f7abd5917001a56bd"
OWNER="fscfede-beep"
def rv(login="reviewer-alpha", state="APPROVED", commit_id=HEAD, rid=4):
    return {"id":rid,"user":{"login":login,"type":"User"},"state":state,
            "commit_id":commit_id,"submitted_at":"2026-11-08T05:00:00Z"}

class ReviewProvenanceTests(unittest.TestCase):
    def subject(self, reviews, permission="write"):
        obj=RealEvidence(ROOT,runner=object())
        def responder(args):
            ep=str(args[-1])
            if "/reviews?" in ep: return reviews
            if "/permission" in ep: return {"permission": permission}
            raise AssertionError("unexpected endpoint "+ep)
        obj._json=responder
        return obj

    def test_empty_review_history_no_authority(self):
        self.assertIsNone(self.subject([]).independent_review_receipt(374,HEAD,OWNER))

    def test_author_approval_no_authority(self):
        self.assertIsNone(self.subject([rv(login=OWNER)]).independent_review_receipt(374,HEAD,OWNER))

    def test_old_head_approval_no_authority(self):
        self.assertIsNone(self.subject([rv(commit_id="1"*40)]).independent_review_receipt(374,HEAD,OWNER))

    def test_unprivileged_reviewer_no_authority(self):
        self.assertIsNone(self.subject([rv()],permission="read").independent_review_receipt(374,HEAD,OWNER))

    def test_latest_review_dismissed_no_authority(self):
        rows=[rv(rid=1),rv(rid=2,state="DISMISSED")]
        self.assertIsNone(self.subject(rows).independent_review_receipt(374,HEAD,OWNER))

    def test_changes_requested_blocks_another_approval(self):
        rows=[rv(),rv(login="other-reviewer",state="CHANGES_REQUESTED",rid=6)]
        self.assertIsNone(self.subject(rows).independent_review_receipt(374,HEAD,OWNER))

    def test_exhaustiveness_required(self):
        rows=[rv(rid=i+1) for i in range(100)]
        with self.assertRaisesRegex(EvidenceError,"exhaustive"):
            self.subject(rows).independent_review_receipt(374,HEAD,OWNER)

    def test_exact_head_write_permission_returns_bounded_receipt(self):
        got=self.subject([rv()],permission="maintain").independent_review_receipt(374,HEAD,OWNER)
        self.assertEqual((got["commit_id"],got["reviewer"],got["review_id"],got["permission"]),
                         (HEAD,"reviewer-alpha",4,"maintain"))

if __name__=="__main__":
    unittest.main()
