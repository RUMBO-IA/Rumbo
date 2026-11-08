"""R8 PUBLIC security invariants for Vercel branch-suppression vs required check.

No network calls, deployment, or modification of vercel.json.
"""
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from public_vercel_gate_audit import deployment_enabled,required_vercel_check_feasibility

CONFIG=json.loads((ROOT/"vercel.json").read_text(encoding="utf-8"))
BRANCH374="fix/privacy-boundary-clean-successor-20261108"
BRANCH373="rescue/pr367-privacy-clean-20261107"

class VercelGateSatisfiabilityTests(unittest.TestCase):
    def test_real_374_branch_is_explicitly_disabled(self):
        self.assertIs(deployment_enabled(CONFIG,BRANCH374),False)

    def test_real_373_rescue_branch_is_enabled_by_default(self):
        self.assertIs(deployment_enabled(CONFIG,BRANCH373),True)

    def test_real_protected_main_is_disabled(self):
        self.assertIs(deployment_enabled(CONFIG,"main"),False)

    def test_374_required_vercel_is_unsatisfied_by_automatic_deploy(self):
        report=required_vercel_check_feasibility(CONFIG,BRANCH374,("privacy","Vercel"))
        self.assertTrue(report["policy_conflict"])
        self.assertEqual(report["classification"],"BLOCKED_POLICY")
        self.assertFalse(report["automatic_deployment_enabled"])

    def test_true_override_wins_over_matching_false(self):
        cfg={"git":{"deploymentEnabled":{"fix/privacy-*":False,
                 "fix/privacy-boundary-*":True}}}
        self.assertIs(deployment_enabled(cfg,BRANCH374),True)

    def test_unspecified_branch_is_enabled(self):
        cfg={"git":{"deploymentEnabled":{"research/*":False}}}
        self.assertIs(deployment_enabled(cfg,BRANCH374),True)

    def test_global_disabled_is_disabled(self):
        self.assertIs(deployment_enabled({"git":{"deploymentEnabled":False}},BRANCH374),False)

    def test_unrecognized_glob_must_not_assert_enabled(self):
        cfg={"git":{"deploymentEnabled":{"fix/**/boundary-*":False}}}
        self.assertIsNone(deployment_enabled(cfg,BRANCH374))

    def test_required_vercel_not_present_means_no_required_check_conflict(self):
        report=required_vercel_check_feasibility(CONFIG,BRANCH374,("privacy",))
        self.assertFalse(report["policy_conflict"])

    def test_missing_configuration_uses_documented_default_enabled(self):
        self.assertIs(deployment_enabled({},BRANCH374),True)

if __name__=="__main__":
    unittest.main()
