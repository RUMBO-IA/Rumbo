import unittest
from scripts import verify_live_production_lock as live

LOCK = {
    "application_sha": "34c625c65e047fdec06a5bef7064d2de6bed48ba",
    "deployment_id": "dpl_8KbqvsKuua22xK4EQYZmtF3KXmNK",
    "domain": "rumbo.verso.fans",
}
INSPECT = {
    "id": "dpl_8KbqvsKuua22xK4EQYZmtF3KXmNK",
    "target": "production",
    "readyState": "READY",
}
META = {
    "id": "dpl_8KbqvsKuua22xK4EQYZmtF3KXmNK",
    "target": "production",
    "readyState": "READY",
    "meta": {"githubCommitSha": "34c625c65e047fdec06a5bef7064d2de6bed48ba"},
}

class LiveProductionLockTests(unittest.TestCase):
    def test_exact_binding_passes(self):
        self.assertEqual([], live.evaluate(LOCK, INSPECT, META))

    def test_alias_deployment_drift_fails(self):
        observed = dict(INSPECT); observed["id"] = "dpl_other"
        self.assertTrue(any("alias deployment" in e for e in live.evaluate(LOCK, observed, META)))

    def test_metadata_deployment_drift_fails(self):
        observed = dict(META); observed["id"] = "dpl_other"
        self.assertTrue(any("metadata deployment" in e for e in live.evaluate(LOCK, INSPECT, observed)))

    def test_git_sha_drift_fails(self):
        observed = dict(META); observed["meta"] = {"githubCommitSha": "0" * 40}
        self.assertTrue(any("Git SHA" in e for e in live.evaluate(LOCK, INSPECT, observed)))

    def test_nonproduction_target_fails(self):
        observed = dict(INSPECT); observed["target"] = "preview"
        self.assertTrue(any("target" in e for e in live.evaluate(LOCK, observed, META)))

    def test_not_ready_fails(self):
        observed = dict(META); observed["readyState"] = "ERROR"
        self.assertTrue(any("ready state" in e for e in live.evaluate(LOCK, INSPECT, observed)))

if __name__ == "__main__":
    unittest.main()