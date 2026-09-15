from __future__ import annotations

import json
import pathlib
import shutil
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from scripts import verify_content_execution_grant as grant_verify

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = (
    "CONTENT_EXECUTION_GRANT_POLICY_V1.json",
    "CONTENT_EXECUTION_GRANT_SCHEMA_V1.json",
    "content_execution_grants_v1.json",
    "content_registry_v2.json",
    "content_human_decision_observations_v1.json",
    "content_publication_observations_v1.json",
    "distribution_lock_v1.json",
)


def make_root(tmp: str) -> pathlib.Path:
    root = pathlib.Path(tmp)
    brand = root / "docs" / "brand"
    brand.mkdir(parents=True)
    for name in FILES:
        shutil.copy2(ROOT / "docs" / "brand" / name, brand / name)
    return root


def load(root: pathlib.Path, name: str) -> dict:
    return json.loads((root / "docs" / "brand" / name).read_text(encoding="utf-8"))


def save(root: pathlib.Path, name: str, data: dict) -> None:
    (root / "docs" / "brand" / name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def grant(root: pathlib.Path) -> dict:
    return load(root, "content_execution_grants_v1.json")["grants"][-1]


def make_terminal(root: pathlib.Path, status: str = "EXPIRED") -> dict:
    data = load(root, "content_execution_grants_v1.json")
    g = data["grants"][-1]
    g["status"] = status
    g["scoped_agent_execution_authorized"] = False
    g["status_changed_at"] = "2026-09-15T02:26:00-03:00"
    g["status_reason"] = "synthetic terminal test"
    save(root, "content_execution_grants_v1.json", data)
    return g


class ContentExecutionGrantTests(unittest.TestCase):
    def test_baseline_active_passes(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(grant_verify.verify(make_root(td)), [])

    def test_scope_cannot_expand(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][-1]["item_allowlist"].append("W2-01")
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("issuance snapshot" in e or "scope_sha256" in e for e in grant_verify.verify(root)))

    def test_auto_publish_cannot_enable(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][-1]["auto_publish"] = "GO"
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("AUTO_PUBLISH" in e for e in grant_verify.verify(root)))

    def test_standing_permission_forbidden(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][-1]["standing_permission"] = True
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("standing permission" in e for e in grant_verify.verify(root)))

    def test_base_agent_permission_remains_false(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][-1]["base_agent_may_publish"] = True
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("base agent permission" in e for e in grant_verify.verify(root)))

    def test_account_identity_bound_to_linkedin_company(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][-1]["account_identity"] = "company:999:wrong"
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("account identity" in e for e in grant_verify.verify(root)))

    def test_publication_decision_must_cover_grant(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_human_decision_observations_v1.json")
            obs = next(o for o in data["observations"] if o.get("observation_id") == "decision-publication-authorization-r26-20260913-001")
            obs["item_ids"] = ["W1-03"]
            save(root, "content_human_decision_observations_v1.json", data)
            self.assertTrue(any("does not cover all grant items" in e for e in grant_verify.verify(root)))

    def test_override_decision_must_cover_grant(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_human_decision_observations_v1.json")
            obs = next(o for o in data["observations"] if o.get("observation_id") == "decision-one-shot-agent-override-r26-20260913-001")
            obs["target_channels"] = ["X"]
            save(root, "content_human_decision_observations_v1.json", data)
            self.assertTrue(any("does not cover all grant channels" in e for e in grant_verify.verify(root)))

    def test_active_scope_must_equal_current_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][-1]["item_allowlist"].append("W2-01")
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("ACTIVE grant scope must equal exact current unobserved" in e for e in grant_verify.verify(root)))

    def test_terminal_grant_cannot_execute(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            make_terminal(root)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][-1]["scoped_agent_execution_authorized"] = True
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("terminal grant must not authorize execution" in e for e in grant_verify.verify(root)))

    def test_terminal_grant_requires_terminal_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            make_terminal(root)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][-1].pop("status_reason")
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("status_reason" in e for e in grant_verify.verify(root)))

    def test_expired_status_changed_at_cannot_predate_expiry(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            make_terminal(root)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][-1]["status_changed_at"] = "2026-09-15T02:24:59-03:00"
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("status_changed_at cannot predate expires_at" in e for e in grant_verify.verify(root)))

    def test_consumed_requires_zero_current_missing_targets(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            make_terminal(root, "CONSUMED")
            self.assertTrue(any("CONSUMED grant requires zero current missing targets" in e for e in grant_verify.verify(root)))

    def test_issuance_snapshot_hash_rejects_counter_rewrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][-1]["observed_logical_targets_before_grant"] = 7
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("issuance snapshot differs" in e for e in grant_verify.verify(root)))

    def test_missing_target_outside_issuance_scope_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            data["observations"] = [o for o in data["observations"] if not (o.get("item_id") == "W1-01" and o.get("channel") == "LinkedIn")]
            data["coverage"]["logical_targets_observed"] = 7
            data["coverage"]["physical_remote_records"] = 9
            save(root, "content_publication_observations_v1.json", data)
            self.assertTrue(any("outside immutable issuance scope" in e or "ACTIVE grant scope must equal exact current unobserved" in e for e in grant_verify.verify(root)))

    def test_policy_pins_r26_issuance(self):
        policy = load(ROOT, "CONTENT_EXECUTION_GRANT_POLICY_V1.json")
        self.assertEqual(policy["active_authority_anchor_commit"], "c277753a8ba8e3a770daf928d88603355fe2413f")
        self.assertEqual(policy["active_grant_issuance_commit"], "b9b29f40204ee24ee873df253b7bb505080813cd")
        self.assertEqual(policy["active_grant_issuance_state_sha256"], "29d807872b12e2a2003ec1c1d54caad2b83276d3daf7c11f675a4b6d6b1eee55")

    def test_r26_exact_scope_and_identity(self):
        with tempfile.TemporaryDirectory() as td:
            g = grant(make_root(td))
            self.assertEqual(g["grant_id"], "content-linkedin-r26-one-shot-20260914-001")
            self.assertEqual(g["item_allowlist"], ["W1-03", "W2-02"])
            self.assertEqual(g["channel_allowlist"], ["LinkedIn"])
            self.assertEqual(g["account_identity"], "company:145014017:rumbo-ia")
            self.assertEqual(g["remaining_logical_target_limit"], 2)
            self.assertTrue(g["scoped_agent_execution_authorized"])
            self.assertFalse(g["standing_permission"])
            self.assertEqual(g["auto_publish"], "NO_GO")

    def test_terminal_grant_preserves_issuance_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            make_terminal(root)
            g = grant(root)
            self.assertEqual(g["item_allowlist"], ["W1-03", "W2-02"])
            self.assertEqual(g["observed_logical_targets_before_grant"], 8)
            self.assertEqual(g["remaining_logical_target_limit"], 2)
            self.assertEqual(g["scope_sha256"], "d7db98a025216baf4f3ce1fe0d1a0107878e3517d85c793808adc66e901fc632")

    def test_required_git_read_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / ".git").mkdir()
            failed = SimpleNamespace(returncode=128, stdout="", stderr="fatal")
            with mock.patch.object(grant_verify.subprocess, "run", return_value=failed):
                with self.assertRaises(ValueError):
                    grant_verify._git_json(root, "deadbeef", grant_verify.DECISIONS, required=True)

    def test_optional_git_read_can_skip_missing_history(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / ".git").mkdir()
            failed = SimpleNamespace(returncode=128, stdout="", stderr="fatal")
            with mock.patch.object(grant_verify.subprocess, "run", return_value=failed):
                self.assertIsNone(grant_verify._git_json(root, "HEAD^", grant_verify.GRANTS))


if __name__ == "__main__":
    unittest.main()
