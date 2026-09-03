import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "scope_guard.py"
SPEC = importlib.util.spec_from_file_location("scope_guard", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


class ScopeGuardTests(unittest.TestCase):
    def test_unscoped_target_is_rejected(self):
        result = MOD.evaluate(
            {
                "target_scope_binding": False,
                "target_identity": "candidate-A",
                "promotion_decision": "NO_RESULT",
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn(
            "UNSCOPED_FIELD_FORBIDDEN:target_identity",
            result["errors"],
        )

    def test_scope_requires_evidence(self):
        result = MOD.evaluate(
            {
                "target_scope_binding": True,
                "promotion_decision": "NO_RESULT",
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn("SCOPE_EVIDENCE_REQUIRED", result["errors"])

    def test_scoped_incomplete_is_not_verified(self):
        result = MOD.evaluate(
            {
                "transport_handshake": True,
                "target_scope_binding": True,
                "target_scope_evidence": "explicit-target-proof",
                "promotion_decision": "NO_RESULT",
            }
        )
        self.assertEqual(
            {"ok": True, "decision": "SCOPED_NOT_VERIFIED", "errors": []},
            result,
        )

    def test_contaminated_target_is_rejected(self):
        result = MOD.evaluate(
            {
                "contaminated": True,
                "target_scope_binding": False,
                "target_identity": "must-reset",
                "promotion_decision": "VERIFIED",
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn("CONTAMINATED_TARGET_MUST_RESET", result["errors"])
        self.assertIn("CONTAMINATED_PROMOTION_FORBIDDEN", result["errors"])

    def test_transport_race_aborts(self):
        result = MOD.evaluate(
            {
                "transport_advertised_online": True,
                "transport_handshake": False,
                "target_scope_binding": False,
                "promotion_decision": "NO_RESULT",
            }
        )
        self.assertFalse(result["ok"])
        self.assertIn("TRANSPORT_RACE_ABORTED", result["errors"])

    def test_complete_chain_can_verify(self):
        receipt = {
            "transport_advertised_online": True,
            "transport_handshake": True,
            "target_scope_binding": True,
            "target_scope_evidence": "explicit-target-proof",
            "target_identity": "target-A",
            "primary_evidence": {"observed": True},
            "direct_binding": {"verified": True},
            "promotion_decision": "VERIFIED",
        }
        self.assertEqual(
            {"ok": True, "decision": "VERIFIED", "errors": []},
            MOD.evaluate(receipt),
        )

    def test_verified_missing_binding_fails(self):
        receipt = {
            "transport_handshake": True,
            "target_scope_binding": True,
            "target_scope_evidence": "explicit-target-proof",
            "target_identity": "target-A",
            "primary_evidence": {"observed": True},
            "promotion_decision": "VERIFIED",
        }
        result = MOD.evaluate(receipt)

        self.assertFalse(result["ok"])
        self.assertIn("VERIFIED_MISSING:direct_binding", result["errors"])


if __name__ == "__main__":
    unittest.main()
