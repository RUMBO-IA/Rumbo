import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANCHOR = ROOT / "governance" / "CONTROL_PLANE_AUTHORITY_V1.json"
VERIFIER = ROOT / "scripts" / "verify_control_plane_authority_anchor.py"

class ControlPlaneAuthorityAnchorTests(unittest.TestCase):
    def test_anchor_exists_and_fails_closed(self):
        self.assertTrue(ANCHOR.is_file(), "protected public control-plane authority anchor is missing")
        data = json.loads(ANCHOR.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "rumbo.control-plane-authority/v1")
        self.assertEqual(data["authority_repository"], "RUMBO-IA/Rumbo")
        self.assertEqual(data["source_repository"], "RUMBO-IA/rumbo-control-queue")
        self.assertRegex(data["canonical_source_commit"], r"^[0-9a-f]{40}$")
        self.assertRegex(data["canonical_source_tree"], r"^[0-9a-f]{40}$")
        self.assertFalse(data["source_branch_is_authority"])
        self.assertEqual(data["production"], "NO_GO")
        self.assertEqual(data["external_spend_usd"], 0)
        self.assertEqual(data["authority_rule"], "ONLY_THIS_PROTECTED_PUBLIC_ANCHOR_SELECTS_CANONICAL_PRIVATE_COMMITS")

    def test_verifier_cli_accepts_current_anchor_offline(self):
        result = subprocess.run(
            [sys.executable, str(VERIFIER), "--anchor", str(ANCHOR), "--offline"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["mode"], "offline")

    def test_verifier_cli_rejects_tampered_source_commit(self):
        data = json.loads(ANCHOR.read_text(encoding="utf-8"))
        data["canonical_source_commit"] = "not-a-sha"
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "anchor.json"
            bad.write_text(json.dumps(data), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VERIFIER), "--anchor", str(bad), "--offline"],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical_source_commit", result.stderr)

if __name__ == "__main__":
    unittest.main()
