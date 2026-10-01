import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANCHOR = ROOT / "docs" / "control-authority-anchor-v1.json"
VERIFIER = ROOT / "scripts" / "verify_control_authority_anchor.py"

spec = importlib.util.spec_from_file_location("verify_control_authority_anchor", VERIFIER)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class ControlAuthorityAnchorTests(unittest.TestCase):
    def load(self):
        return json.loads(ANCHOR.read_text(encoding="utf-8"))

    def test_current_anchor_static_contract(self):
        data = self.load()
        guard.validate_static(data)
        self.assertEqual(
            "68b6ad0b883638f4d5dc15bb4f8e668267cb932e",
            data["subject"]["authorized_main_sha"],
        )
        self.assertEqual(
            "7f9e32478dae0f491fdacc78a2ecfe1f0473af18",
            data["subject"]["authorized_tree_sha"],
        )

    def test_invalid_authorized_commit_fails_closed(self):
        data = self.load()
        data["subject"]["authorized_main_sha"] = "not-a-sha"
        with self.assertRaisesRegex(guard.AnchorError, "authorized_main_sha"):
            guard.validate_static(data)

    def test_invalid_authorized_tree_fails_closed(self):
        data = self.load()
        data["subject"]["authorized_tree_sha"] = "bad-tree"
        with self.assertRaisesRegex(guard.AnchorError, "authorized_tree_sha"):
            guard.validate_static(data)

    def test_source_tree_mismatch_fails_online(self):
        data = self.load()
        original = guard.gh_json
        def fake(endpoint):
            if endpoint.endswith("/git/commits/" + data["subject"]["authorized_main_sha"]):
                return {"tree": {"sha": "0" * 40}}
            raise AssertionError(endpoint)
        guard.gh_json = fake
        try:
            with self.assertRaisesRegex(guard.AnchorError, "authorized_tree_sha mismatch"):
                guard.validate_online(data)
        finally:
            guard.gh_json = original

    def test_private_main_drift_does_not_change_canon(self):
        data = self.load()
        authorized = data["subject"]["authorized_main_sha"]
        tree = data["subject"]["authorized_tree_sha"]
        original = guard.gh_json

        def fake(endpoint):
            if endpoint.endswith("/git/commits/" + authorized):
                return {"tree": {"sha": tree}}
            if endpoint == "repos/RUMBO-IA/Rumbo/branches/main":
                return {
                    "protected": True,
                    "protection": {
                        "required_status_checks": {
                            "contexts": ["privacy", "Vercel"]
                        }
                    },
                }
            if endpoint == "repos/RUMBO-IA/Rumbo/rulesets/22317339":
                return {
                    "enforcement": "active",
                    "bypass_actors": [],
                    "rules": [{"type": "non_fast_forward"}],
                }
            if endpoint == "repos/RUMBO-IA/rumbo-control-queue/branches/main":
                return {"commit": {"sha": "f" * 40}, "protected": False}
            raise AssertionError(endpoint)

        guard.gh_json = fake
        try:
            observed = guard.validate_online(data)
        finally:
            guard.gh_json = original

        self.assertFalse(observed["source_branch_matches_anchor"])
        self.assertEqual(authorized, observed["canonical_source_commit"])
        self.assertEqual(tree, observed["canonical_source_tree"])

    def test_unprotected_public_authority_fails(self):
        data = self.load()
        authorized = data["subject"]["authorized_main_sha"]
        tree = data["subject"]["authorized_tree_sha"]
        original = guard.gh_json
        def fake(endpoint):
            if endpoint.endswith("/git/commits/" + authorized):
                return {"tree": {"sha": tree}}
            if endpoint == "repos/RUMBO-IA/Rumbo/branches/main":
                return {"protected": False}
            raise AssertionError(endpoint)
        guard.gh_json = fake
        try:
            with self.assertRaisesRegex(guard.AnchorError, "public authority protected=false"):
                guard.validate_online(data)
        finally:
            guard.gh_json = original

    def test_missing_required_check_fails(self):
        data = self.load()
        authorized = data["subject"]["authorized_main_sha"]
        tree = data["subject"]["authorized_tree_sha"]
        original = guard.gh_json
        def fake(endpoint):
            if endpoint.endswith("/git/commits/" + authorized):
                return {"tree": {"sha": tree}}
            if endpoint == "repos/RUMBO-IA/Rumbo/branches/main":
                return {
                    "protected": True,
                    "protection": {
                        "required_status_checks": {"contexts": ["privacy"]}
                    },
                }
            raise AssertionError(endpoint)
        guard.gh_json = fake
        try:
            with self.assertRaisesRegex(guard.AnchorError, "missing required checks:Vercel"):
                guard.validate_online(data)
        finally:
            guard.gh_json = original

    def test_ruleset_bypass_fails(self):
        data = self.load()
        authorized = data["subject"]["authorized_main_sha"]
        tree = data["subject"]["authorized_tree_sha"]
        original = guard.gh_json
        def fake(endpoint):
            if endpoint.endswith("/git/commits/" + authorized):
                return {"tree": {"sha": tree}}
            if endpoint == "repos/RUMBO-IA/Rumbo/branches/main":
                return {
                    "protected": True,
                    "protection": {
                        "required_status_checks": {
                            "contexts": ["privacy", "Vercel"]
                        }
                    },
                }
            if endpoint == "repos/RUMBO-IA/Rumbo/rulesets/22317339":
                return {
                    "enforcement": "active",
                    "bypass_actors": [{"actor_id": 1}],
                    "rules": [{"type": "non_fast_forward"}],
                }
            raise AssertionError(endpoint)
        guard.gh_json = fake
        try:
            with self.assertRaisesRegex(guard.AnchorError, "bypass_actors"):
                guard.validate_online(data)
        finally:
            guard.gh_json = original


if __name__ == "__main__":
    unittest.main()
