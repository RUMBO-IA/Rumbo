import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import autonomy_surface_guard as guard

AUTHORITY = {
    "surfaces": {
        "brave": {"capabilities": ["READ", "WRITE"], "effects": ["LOCAL_UI"]},
        "github": {"capabilities": ["READ", "WRITE"], "effects": ["REMOTE_MUTATION"]},
    }
}

class AutonomySurfaceGuardTests(unittest.TestCase):
    def test_authorized_exposed_surface_is_allowed(self):
        result = guard.evaluate(AUTHORITY, {"surface": "brave", "capability": "WRITE", "effect": "LOCAL_UI"})
        self.assertEqual(result["state"], "ALLOW")

    def test_observed_surface_cannot_create_authority(self):
        result = guard.evaluate(AUTHORITY, {"surface": "desktop", "capability": "WRITE", "effect": "LOCAL_UI", "observed_available": True})
        self.assertEqual(result["state"], "SAFE_STOP")
        self.assertIn("SURFACE_AUTHORITY_REQUIRED", result["errors"])

    def test_capability_must_be_explicitly_granted(self):
        result = guard.evaluate(AUTHORITY, {"surface": "brave", "capability": "EXECUTE", "effect": "LOCAL_UI"})
        self.assertIn("CAPABILITY_AUTHORITY_MISMATCH", result["errors"])

    def test_effect_scope_must_be_explicitly_granted(self):
        result = guard.evaluate(AUTHORITY, {"surface": "brave", "capability": "WRITE", "effect": "REMOTE_MUTATION"})
        self.assertIn("EFFECT_AUTHORITY_MISMATCH", result["errors"])

    def test_missing_authority_fails_closed(self):
        result = guard.evaluate({}, {"surface": "brave", "capability": "READ", "effect": "LOCAL_UI"})
        self.assertEqual(result["state"], "SAFE_STOP")
        self.assertIn("SURFACE_AUTHORITY_REQUIRED", result["errors"])

    def test_wildcards_are_not_accepted(self):
        authority = {"surfaces": {"*": {"capabilities": ["*"], "effects": ["*"]}}}
        result = guard.evaluate(authority, {"surface": "brave", "capability": "WRITE", "effect": "LOCAL_UI"})
        self.assertEqual(result["state"], "SAFE_STOP")

if __name__ == "__main__":
    unittest.main()
