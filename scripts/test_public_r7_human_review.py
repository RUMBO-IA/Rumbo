"""Security regression: automated bot reviews are not human merge authority."""
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from test_real_review_provenance_public_r4 import ReviewProvenanceTests, HEAD, OWNER, rv

class HumanReviewBoundaryTests(unittest.TestCase):
    def review(self, *, user_type="User"):
        review=rv(login="independent-reviewer",state="APPROVED",commit_id=HEAD,rid=202)
        if user_type is None:
            review["user"].pop("type", None)
        else:
            review["user"]["type"]=user_type
        return review

    def test_approved_bot_with_write_permission_not_human_authority(self):
        evidence=ReviewProvenanceTests().subject([self.review(user_type="Bot")],permission="admin")
        self.assertIsNone(evidence.independent_review_receipt(374,HEAD,OWNER))

    def test_approved_identity_without_type_fails_closed(self):
        evidence=ReviewProvenanceTests().subject([self.review(user_type=None)],permission="write")
        self.assertIsNone(evidence.independent_review_receipt(374,HEAD,OWNER))

    def test_user_approved_exact_head_write_is_accepted(self):
        evidence=ReviewProvenanceTests().subject([self.review(user_type="User")],permission="write")
        receipt=evidence.independent_review_receipt(374,HEAD,OWNER)
        self.assertIsNotNone(receipt)
        self.assertEqual((receipt["reviewer"],receipt["commit_id"]),("independent-reviewer",HEAD))

if __name__=="__main__":
    unittest.main()
