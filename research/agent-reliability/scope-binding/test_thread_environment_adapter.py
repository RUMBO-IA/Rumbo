import unittest

from thread_environment_adapter import evaluate_thread_environments


AUTHORITY = {
    "scope_id": "project-b",
    "source": "trusted-project-selection",
    "environment_id": "env-b",
    "resolved_cwd": "/work/project-b",
    "resolved_workspace_roots": ["/work/project-b"],
}


class ThreadEnvironmentAdapterTests(unittest.TestCase):
    def test_selection_without_connection_proof_does_not_verify_runtime(self):
        result = evaluate_thread_environments(
            AUTHORITY,
            [{
                "environmentId": "env-b",
                "cwd": "/work/project-b",
                "runtimeWorkspaceRoots": ["/work/project-b"],
            }],
            runtime_connected=False,
        )
        self.assertFalse(result["ok"])
        self.assertEqual("SELECTION_ONLY", result["decision"])

    def test_wrong_selected_environment_is_rejected(self):
        result = evaluate_thread_environments(
            AUTHORITY,
            [{
                "environmentId": "env-a",
                "cwd": "/work/project-a",
                "runtimeWorkspaceRoots": ["/work/project-a"],
            }],
            runtime_connected=True,
        )
        self.assertFalse(result["ok"])
        self.assertIn("ENVIRONMENT_AUTHORITY_MISMATCH", result["errors"])

    def test_matching_selection_plus_connection_proof_is_bound(self):
        result = evaluate_thread_environments(
            AUTHORITY,
            [{
                "environmentId": "env-b",
                "cwd": "/work/project-b",
                "runtimeWorkspaceRoots": ["/work/project-b"],
            }],
            runtime_connected=True,
        )
        self.assertEqual(
            {"ok": True, "decision": "RUNTIME_SCOPE_BOUND", "errors": []},
            result,
        )


if __name__ == "__main__":
    unittest.main()
