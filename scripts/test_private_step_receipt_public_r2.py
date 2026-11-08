"""Adversarial receipts: a green public job must not impersonate private attestation.

Independent PUBLIC-lane isolation test. No network calls and no secrets.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import safe_merge_evidence as evidence
import safe_merge_policy as policy

HEAD = "3fee7db5677e50a7637f7e3f7abd5917001a56bd"
BRANCH = "fix/privacy-boundary-clean-successor-20261108"
RUN = 42446970643


class PrivateStepReceiptTests(unittest.TestCase):
    def subject(self, *, conclusion="skipped", job_head=HEAD, include_step=True):
        obj = evidence.RealEvidence(ROOT, runner=object())
        # Keep workflow-integrity validation unchanged; isolate just the attestation seam.
        obj.workflow_blob = lambda _: {
            "path": policy.DEFAULT_POLICY.privacy_workflow_path,
            "git_blob": policy.DEFAULT_POLICY.privacy_workflow_blob,
            "sha256": policy.DEFAULT_POLICY.privacy_workflow_sha256,
        }
        run = {
            "id": RUN,
            "workflow_id": policy.DEFAULT_POLICY.privacy_workflow_id,
            "path": policy.DEFAULT_POLICY.privacy_workflow_path,
            "event": "pull_request",
            "status": "completed",
            "conclusion": "success",
            "head_sha": HEAD,
            "head_branch": BRANCH,
            "pull_requests": [{"number": 374}],
            "run_attempt": 1,
            "created_at": "2026-11-08T04:28:39Z",
        }
        job = {
            "id": 128627847678,
            "run_id": RUN,
            "head_sha": job_head,
            "name": "privacy",
            "status": "completed",
            "conclusion": "success",
            "steps": ([{
                "name": "Verify public privacy invariants (trusted main only)",
                "status": "completed",
                "conclusion": conclusion,
            }] if include_step else []),
        }
        def query(args):
            ep = next((str(x) for x in args if str(x).startswith("repos/RUMBO-IA/Rumbo/")), "")
            if "/actions/workflows/" in ep and ep.endswith("/runs"):
                return {"total_count": 1, "workflow_runs": [run]}
            if ep.endswith(f"/actions/runs/{RUN}"):
                return run
            if ep.endswith(f"/actions/runs/{RUN}/jobs?per_page=100"):
                return {"total_count": 1, "jobs": [job]}
            raise AssertionError(f"unexpected network seam: {args}")
        obj._json = query
        return obj

    def test_public_success_without_independent_app_is_rejected(self):
        obj = self.subject(conclusion="skipped")
        with self.assertRaisesRegex(evidence.EvidenceError, "independent trusted"):
            obj.privacy_attestation(374, HEAD, "main", BRANCH)
        with self.assertRaisesRegex(evidence.EvidenceError, "private privacy step"):
            obj._require_executed_private_step(RUN, HEAD)

    def test_post_write_revalidation_rejects_skipped_private_step(self):
        obj = self.subject(conclusion="skipped")
        previous = {"run_id": RUN, "run_attempt": 1, "created_at": "2026-11-08T04:28:39Z"}
        with self.assertRaisesRegex(evidence.EvidenceError, "independent trusted"):
            obj.privacy_attestation_by_run(previous, HEAD, "main", BRANCH)

    def test_private_step_missing_is_rejected(self):
        obj = self.subject(include_step=False)
        with self.assertRaisesRegex(evidence.EvidenceError, "private privacy step"):
            obj._require_executed_private_step(RUN, HEAD)

    def test_job_head_must_match_exact_pr_head(self):
        obj = self.subject(conclusion="success", job_head="0" * 40)
        with self.assertRaisesRegex(evidence.EvidenceError, "exact HEAD"):
            obj._require_executed_private_step(RUN, HEAD)

    def test_explicitly_failed_private_step_is_rejected(self):
        obj = self.subject(conclusion="failure")
        with self.assertRaisesRegex(evidence.EvidenceError, "private privacy step"):
            obj._require_executed_private_step(RUN, HEAD)

    def test_matching_executed_private_step_is_diagnostic_only(self):
        obj = self.subject(conclusion="success")
        self.assertIsNone(obj._require_executed_private_step(RUN, HEAD))
        with self.assertRaisesRegex(evidence.EvidenceError, "independent trusted"):
            obj.privacy_attestation(374, HEAD, "main", BRANCH)


if __name__ == "__main__":
    unittest.main()
