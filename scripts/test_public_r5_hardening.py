"""PUBLIC R5: no network/no write adversarial review and exact-lease tests."""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_real_review_provenance_public_r4 import ReviewProvenanceTests, HEAD, rv
from test_safe_merge_authority import FakeRunner, ROOT, policy, evidence, BASE
from safe_merge_evidence import RealEvidence


class PublicReviewR5Tests(unittest.TestCase):
    def subject(self, reviews, permission="write"):
        return ReviewProvenanceTests().subject(reviews, permission=permission)

    def test_case_variant_self_review_must_not_authorize(self):
        subject = self.subject([rv(login="Reviewer-Alpha")])
        self.assertIsNone(subject.independent_review_receipt(374, HEAD, "reviewer-alpha"))

    def test_later_dismissal_wins_even_if_api_order_reversed(self):
        later = rv(login="Reviewer-Alpha", state="DISMISSED", rid=22)
        later["submitted_at"] = "2026-11-08T07:00:00Z"
        earlier = rv(login="reviewer-alpha", state="APPROVED", rid=20)
        earlier["submitted_at"] = "2026-11-08T06:00:00Z"
        self.assertIsNone(self.subject([later, earlier]).independent_review_receipt(
            374, HEAD, "different-author"
        ))

    def test_missing_cross_repo_status_denied(self):
        subject = RealEvidence(ROOT, runner=object())
        subject._json = lambda args: {
            "number": 374, "state": "OPEN", "baseRefName": "main", "headRefName": "test",
            "headRefOid": HEAD, "headRepository": {"nameWithOwner": "RUMBO-IA/Rumbo"},
            "isDraft": False, "author": {"login": "someone"},
        }
        self.assertIsNone(subject.pr(374)["cross"])

    def test_fast_forward_requires_ancestor_and_exact_tip_lease(self):
        candidate = "2" * 40
        fake = FakeRunner({
            ("git", "check-ref-format"): "",
            ("git", "merge-base", "--is-ancestor"): "",
            ("git", "push"): "",
        })
        subject = RealEvidence(ROOT, fake, policy.DEFAULT_POLICY)
        subject.target_sha = lambda target: BASE
        subject.fast_forward("main", BASE, candidate)
        ancestry = ("git", "merge-base", "--is-ancestor", BASE, candidate)
        push = ("git", "push", f"--force-with-lease=refs/heads/main:{BASE}",
                "origin", f"{candidate}:refs/heads/main")
        self.assertIn(ancestry, fake.calls)
        self.assertIn(push, fake.calls)
        self.assertLess(fake.calls.index(ancestry), fake.calls.index(push))
        self.assertFalse(push[-1].startswith("+"))

    def test_divergent_candidate_rejected_before_push(self):
        fake = FakeRunner({
            ("git", "check-ref-format"): "",
            ("git", "merge-base", "--is-ancestor"): evidence.CommandResult(
                ("git", "merge-base", "--is-ancestor"), 1, "", "not ancestor"
            ),
            ("git", "push"): "",
        })
        subject = RealEvidence(ROOT, fake, policy.DEFAULT_POLICY)
        subject.target_sha = lambda target: BASE
        with self.assertRaisesRegex(evidence.EvidenceError, "fast-forward|ancestor"):
            subject.fast_forward("main", BASE, "2"*40)
        self.assertFalse(any(args[:2] == ("git", "push") for args in fake.calls))


if __name__ == "__main__":
    unittest.main()
