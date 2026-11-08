"""PUBLIC R10: fail-closed latest privacy run exact-HEAD proof.

All GitHub responses are local fixtures, all no-write.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from safe_merge_evidence import RealEvidence, EvidenceError
from safe_merge_policy import DEFAULT_POLICY

SHA="a"*40
BRANCH="fix/privacy-boundary-clean-successor-20261108"
PR=374
PATH=DEFAULT_POLICY.privacy_workflow_path
WORKFLOW_ID=DEFAULT_POLICY.privacy_workflow_id


def run(*, rid=123, head=SHA, branch=BRANCH, conclusion="success",
        date="2026-11-08T05:00:00Z", prs=None, attempt=1):
    return {
        "id":rid, "workflow_id":WORKFLOW_ID,"path":PATH,
        "event":"pull_request", "status":"completed","conclusion":conclusion,
        "head_sha":head,"head_branch":branch,"created_at":date,
        "run_attempt":attempt,
        "pull_requests": [{"number":PR}] if prs is None else prs,
    }


class LatestPrivacyEvidenceTests(unittest.TestCase):
    def subject(self, entries, *, count=None, include_count=True, post_run=None):
        obj=RealEvidence(Path(__file__).resolve().parents[1], runner=object())
        obj.workflow_blob=lambda sha:{"path":PATH,"git_blob":"b"*40,"sha256":"c"*64}
        obj._require_independent_privacy_check=lambda sha:{"id":41,"name":"fixture-app",
                   "head_sha":sha,"app_id":777777,"completed_at":"2026-11-08T05:05:00Z"}
        def respond(args):
            endpoint=" ".join(map(str,args))
            if "/actions/workflows/" in endpoint and "/runs" in endpoint:
                value={"workflow_runs":entries}
                if include_count:value["total_count"]=len(entries) if count is None else count
                return value
            if "/actions/runs/123" in endpoint:
                return post_run or run()
            raise AssertionError("unplanned read "+endpoint)
        obj._json=respond
        return obj

    def test_valid_complete_prewrite_run_still_passes(self):
        obj=self.subject([run()])
        att=obj.privacy_attestation(PR,SHA,"main",BRANCH)
        self.assertEqual(att["run_id"],123)

    def test_missing_run_total_count_must_stop(self):
        obj=self.subject([run()],include_count=False)
        with self.assertRaisesRegex(EvidenceError,"incomplete|count"):
            obj.privacy_attestation(PR,SHA,"main",BRANCH)

    def test_truncated_run_page_must_stop(self):
        obj=self.subject([run()],count=101)
        with self.assertRaisesRegex(EvidenceError,"incomplete|truncat"):
            obj.privacy_attestation(PR,SHA,"main",BRANCH)

    def test_wrong_branch_on_matching_pr_run_must_stop(self):
        obj=self.subject([run(branch="unrelated-branch")])
        with self.assertRaisesRegex(EvidenceError,"no exact|branch"):
            obj.privacy_attestation(PR,SHA,"main",BRANCH)

    def test_newest_matching_run_failure_must_stop(self):
        obj=self.subject([run(),run(rid=124,conclusion="failure",
                                  date="2026-11-08T05:30:00Z")])
        with self.assertRaisesRegex(EvidenceError,"newest"):
            obj.privacy_attestation(PR,SHA,"main",BRANCH)

    def test_postwrite_successful_original_run_with_new_failed_run_must_stop(self):
        obj=self.subject([run(),run(rid=124,conclusion="failure",
                                  date="2026-11-08T05:30:00Z")])
        previous={"run_id":123,"run_attempt":1,"created_at":"2026-11-08T05:00:00Z",
                  "pr_number":PR,"independent_privacy_check":
                  obj._require_independent_privacy_check(SHA)}
        with self.assertRaisesRegex(EvidenceError,"newer|latest|supersed"):
            obj.privacy_attestation_by_run(previous,SHA,"main",BRANCH)

    def test_postwrite_unchanged_only_successful_run_passes(self):
        obj=self.subject([run()])
        previous={"run_id":123,"run_attempt":1,"created_at":"2026-11-08T05:00:00Z",
                  "pr_number":PR,"independent_privacy_check":
                  obj._require_independent_privacy_check(SHA)}
        att=obj.privacy_attestation_by_run(previous,SHA,"main",BRANCH)
        self.assertEqual(att["run_id"],123)


if __name__=="__main__":unittest.main()
