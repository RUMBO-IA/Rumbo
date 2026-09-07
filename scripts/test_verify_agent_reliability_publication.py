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


class CandidateInventoryTests(unittest.TestCase):
    def test_candidate_is_exact_skills_only_inventory(self):
        plugin = PUB / "plugin"
        skills = {p.parent.name for p in (plugin / "skills").glob("*/SKILL.md")}
        self.assertEqual(skills, SKILLS)
        self.assertTrue((plugin / ".codex-plugin" / "plugin.json").is_file())
        self.assertTrue((plugin / "assets" / "icon.svg").is_file())
        self.assertTrue((plugin / "assets" / "logo.svg").is_file())
        forbidden = {".app.json", ".mcp.json", "hooks.json"}
        self.assertFalse(any(p.name in forbidden for p in plugin.rglob("*")))

    def test_candidate_skill_bytes_match_bound_source(self):
        import hashlib
        receipt = json.loads((PUB / "source-receipt.json").read_text(encoding="utf-8"))
        for skill, expected in receipt["skill_sha256"].items():
            data = (PUB / "plugin" / "skills" / skill / "SKILL.md").read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected)

    def test_manifest_uses_public_identity_and_live_root_policies(self):
        manifest = json.loads((PUB / "plugin" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["repository"], "https://github.com/RUMBO-IA/Rumbo")
        self.assertNotIn("email", manifest["author"])
        self.assertEqual(manifest["interface"]["displayName"], "RUMBO Agent Reliability")
        self.assertEqual(manifest["interface"]["privacyPolicyURL"], "https://rumbo.verso.fans/openai-privacy")
        self.assertEqual(manifest["interface"]["termsOfServiceURL"], "https://rumbo.verso.fans/openai-terms")


class ReviewerPacketTests(unittest.TestCase):
    def test_listing_has_required_reviewer_fields(self):
        listing = json.loads((PUB / "submission" / "listing.json").read_text(encoding="utf-8"))
        self.assertEqual(listing["display_name"], "RUMBO Agent Reliability")
        self.assertGreaterEqual(len(listing["starter_prompts"]), 3)
        self.assertEqual(listing["availability"]["state"], "UNSET_FAIL_CLOSED")
        self.assertEqual(listing["publisher_urls"]["privacy"], "https://rumbo.verso.fans/openai-privacy")
        self.assertEqual(listing["publisher_urls"]["terms"], "https://rumbo.verso.fans/openai-terms")
        self.assertEqual(listing["publisher_urls"]["support"], "https://rumbo.verso.fans/openai-support")

    def test_reviewer_cases_meet_minimums_and_are_bounded(self):
        packet = json.loads((PUB / "submission" / "reviewer-cases.json").read_text(encoding="utf-8"))
        positive = [c for c in packet["cases"] if c["class"] == "positive"]
        negative = [c for c in packet["cases"] if c["class"] == "negative"]
        self.assertGreaterEqual(len(positive), 5)
        self.assertGreaterEqual(len(negative), 3)
        for case in packet["cases"]:
            self.assertIn(case["expected_skill"], SKILLS | {"NONE"})
            self.assertTrue(case["expected_behavior"])
