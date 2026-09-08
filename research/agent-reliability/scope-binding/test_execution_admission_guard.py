import unittest

import execution_admission_guard as admission


def workspace_receipt():
    return {
        "scope_authority": {
            "scope_id": "project-a",
            "resolved_cwd": "/work/project-a",
            "resolved_workspace_roots": ["/work/project-a"],
            "required_writable_roots": ["/work/project-a"],
            "source": "owner",
        },
        "selected_scope_id": "project-a",
        "session_meta_cwd": "/work/project-a",
        "first_turn_cwd": "/work/project-a",
        "workspace_roots": ["/work/project-a"],
        "writable_roots": ["/work/project-a"],
        "transport_advertised_online": True,
        "transport_handshake": True,
    }


def authority():
    return {"surfaces": {"github": {"capabilities": ["write"], "effects": ["branch"]}}}


class ExecutionAdmissionTests(unittest.TestCase):
    def test_allows_only_when_scope_and_action_authority_pass(self):
        out = admission.evaluate(workspace_receipt(), authority(), {"surface": "github", "capability": "write", "effect": "branch"})
        self.assertEqual(out["state"], "ALLOW")

    def test_scope_failure_blocks_even_with_action_authority(self):
        receipt = workspace_receipt(); receipt["first_turn_cwd"] = "/work/other"
        out = admission.evaluate(receipt, authority(), {"surface": "github", "capability": "write", "effect": "branch"})
        self.assertEqual(out["state"], "SAFE_STOP")
        self.assertIn("FIRST_TURN_CWD_SCOPE_MISMATCH", out["errors"])

    def test_action_failure_blocks_even_with_valid_scope(self):
        out = admission.evaluate(workspace_receipt(), authority(), {"surface": "github", "capability": "admin", "effect": "branch"})
        self.assertEqual(out["state"], "SAFE_STOP")
        self.assertIn("CAPABILITY_AUTHORITY_MISMATCH", out["errors"])

    def test_observed_surface_cannot_replace_authority(self):
        receipt = workspace_receipt(); receipt["observed_surfaces"] = ["github"]
        out = admission.evaluate(receipt, {}, {"surface": "github", "capability": "write", "effect": "branch"})
        self.assertEqual(out["state"], "SAFE_STOP")
        self.assertIn("SURFACE_AUTHORITY_REQUIRED", out["errors"])

    def test_wildcard_does_not_expand_authority(self):
        out = admission.evaluate(workspace_receipt(), {"surfaces": {"github": {"capabilities": ["*"], "effects": ["*"]}}}, {"surface": "github", "capability": "write", "effect": "branch"})
        self.assertEqual(out["state"], "SAFE_STOP")


if __name__ == "__main__":
    unittest.main()
