"""R4 adversarial tests: DRAFT and stale/self review must never permit write.

All GitHub-side effects are mocked via FakeEvidence, no branch writes.
"""
import unittest
from scripts.test_safe_merge_authority import FakeEvidence, merge_request, policy, authority, HEAD


class ReviewEvidence(FakeEvidence):
    def __init__(self, *, draft=False, review_commit=HEAD, reviewer="independent-reviewer",
                 author="fscfede-beep", approved=True, **kw):
        super().__init__(**kw)
        self.draft = draft
        self.review_commit = review_commit
        self.reviewer = reviewer
        self.author = author
        self.approved = approved
        self.review_calls = 0

    def pr(self, number):
        return dict(super().pr(number), draft=self.draft, author=self.author)

    def independent_review_receipt(self, number, expected_head, author):
        self.review_calls += 1
        if not self.approved:
            return None
        return {"commit_id": self.review_commit, "reviewer": self.reviewer,
                "author": self.author, "permission": "write",
                "review_id": 9991, "state": "APPROVED"}


class WriteReviewBoundaryTests(unittest.TestCase):
    def test_wrong_pr_number_is_rejected_before_any_write(self):
        class WrongPr(ReviewEvidence):
            def pr(self, number):
                return dict(super().pr(number), number=999)
        ev = WrongPr()
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev, mode="main")
        self.assertEqual((out.state, out.failed_gate), ("SAFE_STOP", "PR_IDENTITY"))
        self.assertEqual(ev.push_calls, [])

    def test_missing_cross_repository_flag_must_fail_closed(self):
        class MissingCross(ReviewEvidence):
            def pr(self, number):
                value = super().pr(number)
                value.pop("cross", None)
                return value
        ev = MissingCross()
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev, mode="main")
        self.assertEqual((out.state, out.failed_gate), ("SAFE_STOP", "PR_IDENTITY"))
        self.assertEqual(ev.push_calls, [])

    def test_head_repository_drift_on_recheck_must_stop(self):
        class RepoDrift(ReviewEvidence):
            def __init__(self):
                super().__init__()
                self.seen = 0
            def pr(self, number):
                self.seen += 1
                value = super().pr(number)
                if self.seen > 1:
                    value["repo"] = "unexpected/fork"
                return value
        ev = RepoDrift()
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev, mode="main")
        self.assertEqual((out.state, out.failed_gate), ("SAFE_STOP", "INDEPENDENT_REVIEW_RECHECK"))
        self.assertEqual(ev.push_calls, [])

    def test_approval_changed_on_recheck_must_stop(self):
        class ReviewDrift(ReviewEvidence):
            def __init__(self):
                super().__init__()
                self.seen = 0
            def independent_review_receipt(self, number, expected_head, author):
                self.seen += 1
                receipt = super().independent_review_receipt(number, expected_head, author)
                if self.seen > 1:
                    receipt["review_id"] += 1
                return receipt
        ev = ReviewDrift()
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev, mode="main")
        self.assertEqual((out.state, out.failed_gate), ("SAFE_STOP", "INDEPENDENT_REVIEW_RECHECK"))
        self.assertEqual(ev.push_calls, [])

    def test_draft_pr_must_stop_before_any_write(self):
        ev = ReviewEvidence(draft=True)
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev, mode="main")
        self.assertEqual((out.state, out.failed_gate), ("SAFE_STOP", "PR_IDENTITY"))
        self.assertEqual(ev.push_calls, [])

    def test_unknown_draft_status_must_fail_closed(self):
        ev = ReviewEvidence(draft=None)
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev, mode="main")
        self.assertEqual((out.state, out.failed_gate), ("SAFE_STOP", "PR_IDENTITY"))
        self.assertEqual(ev.push_calls, [])

    def test_missing_independent_review_must_stop(self):
        ev = ReviewEvidence(approved=False)
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev, mode="main")
        self.assertEqual((out.state, out.failed_gate), ("SAFE_STOP", "INDEPENDENT_REVIEW"))
        self.assertEqual(ev.push_calls, [])

    def test_stale_approval_must_stop(self):
        ev = ReviewEvidence(review_commit="a"*40)
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev, mode="main")
        self.assertEqual((out.state, out.failed_gate), ("SAFE_STOP", "INDEPENDENT_REVIEW"))
        self.assertEqual(ev.push_calls, [])

    def test_self_approval_must_stop(self):
        ev = ReviewEvidence(reviewer="fscfede-beep")
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev, mode="main")
        self.assertEqual((out.state, out.failed_gate), ("SAFE_STOP", "INDEPENDENT_REVIEW"))
        self.assertEqual(ev.push_calls, [])

    def test_independent_approved_exact_head_preserves_existing_write_path_in_fake(self):
        ev = ReviewEvidence()
        out = authority.evaluate(merge_request(), policy.DEFAULT_POLICY, ev, mode="main")
        self.assertEqual(out.state, "MERGED_SAFE")
        self.assertEqual(ev.push_calls, [("main", "1"*40, HEAD)])


if __name__ == "__main__":
    unittest.main()
