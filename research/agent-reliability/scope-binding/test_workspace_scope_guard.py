import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "workspace_scope_guard.py"
SPEC = importlib.util.spec_from_file_location("workspace_scope_guard", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


def clean_receipt():
    return {
        "scope_authority": {
            "scope_id": "project-b",
            "source": "trusted-project-selection",
            "resolved_cwd": "/work/project-b",
            "resolved_workspace_roots": ["/work/project-b"],
            "allowed_auxiliary_roots": ["/tmp/task-b"],
            "required_writable_roots": ["/work/project-b"],
            "environment_id": "local-b",
        },
        "transport_advertised_online": True,
        "transport_handshake": True,
        "selected_scope_id": "project-b",
        "environment_id": "local-b",
        "session_meta_cwd": "/work/project-b",
        "first_turn_cwd": "/work/project-b",
        "workspace_roots": ["/work/project-b"],
        "writable_roots": ["/work/project-b", "/tmp/task-b"],
        "contaminated": False,
    }

class WorkspaceScopeGuardTests(unittest.TestCase):
    def test_clean_single_root_scope_binds(self):
        self.assertEqual(
            {"ok": True, "decision": "WORKSPACE_SCOPE_BOUND", "errors": []},
            MOD.evaluate_workspace_scope(clean_receipt()),
        )

    def test_environment_resolved_multi_root_scope_binds(self):
        receipt = clean_receipt()
        receipt["scope_authority"]["resolved_workspace_roots"] = [
            "/work/project-b",
            "/work/shared",
        ]
        receipt["scope_authority"]["required_writable_roots"] = [
            "/work/project-b",
            "/work/shared",
        ]
        receipt["workspace_roots"] = ["/work/shared", "/work/project-b"]
        receipt["writable_roots"] = [
            "/work/project-b",
            "/work/shared",
            "/tmp/task-b",
        ]
        self.assertTrue(MOD.evaluate_workspace_scope(receipt)["ok"])

    def test_legacy_project_root_authority_remains_supported(self):
        receipt = clean_receipt()
        receipt["scope_authority"] = {
            "project_root": "/work/project-b",
            "source": "legacy-trusted-selection",
            "allowed_auxiliary_roots": ["/tmp/task-b"],
        }
        receipt["selected_scope_id"] = "/work/project-b"
        receipt.pop("environment_id")
        self.assertTrue(MOD.evaluate_workspace_scope(receipt)["ok"])

    def test_missing_scope_authority_is_rejected(self):
        receipt = clean_receipt()
        del receipt["scope_authority"]
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("SCOPE_AUTHORITY_REQUIRED", result["errors"])

    def test_missing_authority_workspace_roots_is_rejected(self):
        receipt = clean_receipt()
        receipt["scope_authority"]["resolved_workspace_roots"] = []
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("SCOPE_AUTHORITY_WORKSPACE_ROOTS_REQUIRED", result["errors"])

    def test_wrong_selected_scope_is_rejected(self):
        receipt = clean_receipt()
        receipt["selected_scope_id"] = "project-a"
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("SELECTED_SCOPE_AUTHORITY_MISMATCH", result["errors"])

    def test_consistently_wrong_observed_scope_is_rejected(self):
        receipt = clean_receipt()
        receipt.update({
            "selected_scope_id": "project-a",
            "session_meta_cwd": "/work/project-a",
            "first_turn_cwd": "/work/project-a",
            "workspace_roots": ["/work/project-a"],
            "writable_roots": ["/work/project-a"],
        })
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertFalse(result["ok"])
        self.assertIn("SELECTED_SCOPE_AUTHORITY_MISMATCH", result["errors"])

    def test_environment_authority_mismatch_is_rejected(self):
        receipt = clean_receipt()
        receipt["environment_id"] = "local-a"
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("ENVIRONMENT_AUTHORITY_MISMATCH", result["errors"])

    def test_stale_session_cwd_is_rejected(self):
        receipt = clean_receipt()
        receipt["session_meta_cwd"] = "/work/project-a"
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("SESSION_CWD_SCOPE_MISMATCH", result["errors"])

    def test_stale_first_turn_cwd_is_rejected(self):
        receipt = clean_receipt()
        receipt["first_turn_cwd"] = "/work/project-a"
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("FIRST_TURN_CWD_SCOPE_MISMATCH", result["errors"])

    def test_foreign_workspace_root_is_rejected(self):
        receipt = clean_receipt()
        receipt["workspace_roots"].append("/work/project-a")
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("WORKSPACE_ROOTS_SCOPE_MISMATCH", result["errors"])

    def test_workspace_root_order_is_not_authority(self):
        receipt = clean_receipt()
        receipt["scope_authority"]["resolved_workspace_roots"] = [
            "/work/project-b",
            "/work/shared",
        ]
        receipt["workspace_roots"] = ["/work/shared", "/work/project-b"]
        receipt["writable_roots"].append("/work/shared")
        self.assertTrue(MOD.evaluate_workspace_scope(receipt)["ok"])

    def test_foreign_writable_root_is_rejected(self):
        receipt = clean_receipt()
        receipt["writable_roots"].append("/work/project-a")
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("FOREIGN_WRITABLE_ROOT_PRESENT", result["errors"])

    def test_required_writable_root_missing_is_rejected(self):
        receipt = clean_receipt()
        receipt["writable_roots"] = ["/tmp/task-b"]
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("REQUIRED_WRITABLE_ROOT_MISSING", result["errors"])

    def test_read_only_workspace_can_be_authorized(self):
        receipt = clean_receipt()
        receipt["scope_authority"]["required_writable_roots"] = []
        receipt["writable_roots"] = ["/tmp/task-b"]
        self.assertTrue(MOD.evaluate_workspace_scope(receipt)["ok"])

    def test_required_writable_must_be_inside_authority(self):
        receipt = clean_receipt()
        receipt["scope_authority"]["required_writable_roots"] = ["/work/project-a"]
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("AUTHORITY_REQUIRED_WRITABLE_OUTSIDE_SCOPE", result["errors"])

    def test_observed_authority_fields_are_forbidden(self):
        receipt = clean_receipt()
        receipt["allowed_auxiliary_roots"] = ["/work/project-a"]
        receipt["resolved_workspace_roots"] = ["/work/project-a"]
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn(
            "OBSERVED_AUTHORITY_FIELD_FORBIDDEN:allowed_auxiliary_roots",
            result["errors"],
        )
        self.assertIn(
            "OBSERVED_AUTHORITY_FIELD_FORBIDDEN:resolved_workspace_roots",
            result["errors"],
        )

    def test_authority_auxiliary_root_is_accepted(self):
        self.assertTrue(MOD.evaluate_workspace_scope(clean_receipt())["ok"])

    def test_transport_race_is_rejected(self):
        receipt = clean_receipt()
        receipt["transport_handshake"] = False
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("TRANSPORT_RACE_ABORTED", result["errors"])

    def test_contaminated_scope_requires_rebind(self):
        receipt = clean_receipt()
        receipt["contaminated"] = True
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("CONTAMINATED_SCOPE_REQUIRES_REBIND", result["errors"])

    def test_authority_source_is_required(self):
        receipt = clean_receipt()
        receipt["scope_authority"]["source"] = ""
        result = MOD.evaluate_workspace_scope(receipt)
        self.assertIn("SCOPE_AUTHORITY_SOURCE_REQUIRED", result["errors"])

    def test_windows_paths_are_case_insensitive(self):
        receipt = clean_receipt()
        receipt["scope_authority"].update({
            "scope_id": "win-b",
            "resolved_cwd": "C:\\Work\\Project-B",
            "resolved_workspace_roots": [
                "C:\\Work\\Project-B",
                "C:\\Work\\Shared",
            ],
            "allowed_auxiliary_roots": ["C:/Temp/Task-B"],
            "required_writable_roots": ["C:/Work/Project-B"],
            "environment_id": "win-env",
        })
        receipt.update({
            "selected_scope_id": "win-b",
            "environment_id": "win-env",
            "session_meta_cwd": "c:/work/project-b",
            "first_turn_cwd": "C:\\WORK\\PROJECT-B\\",
            "workspace_roots": [
                "c:/work/shared",
                "C:\\work\\project-b",
            ],
            "writable_roots": [
                "c:/WORK/project-b",
                "C:\\Work\\Shared",
                "c:\\temp\\task-b",
            ],
        })
        self.assertTrue(MOD.evaluate_workspace_scope(receipt)["ok"])


if __name__ == "__main__":
    unittest.main()
