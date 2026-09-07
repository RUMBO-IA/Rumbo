import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "openai-publication" / "agent-reliability"
SKILLS = {
    "canonical-state-recovery",
    "deep-research-reconcile",
    "goal-loop-controller",
    "execute-verify-close",
    "audit-final-state",
}


class SourceBindingTests(unittest.TestCase):
    def test_receipt_binds_exact_source_and_five_skills(self):
        receipt = json.loads((PUB / "source-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["source_commit"], "3a7bff2a139cb6840ab6e23a2c19e315000e8b13")
        self.assertEqual(set(receipt["skills"]), SKILLS)
        self.assertRegex(receipt["tree_sha"], r"^[0-9a-f]{40}$")
        self.assertRegex(receipt["manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(set(receipt["skill_sha256"]), SKILLS)
        for digest in receipt["skill_sha256"].values():
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
