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
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class ContentExecutionGrantTests(unittest.TestCase):
    def test_baseline_expired_passes(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(grant_verify.verify(make_root(td)), [])

    def test_scope_cannot_expand(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][0]["item_allowlist"].append("W2-01")
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(
                any(
                    "issuance snapshot" in e or "scope_sha256" in e
                    for e in grant_verify.verify(root)
                )
            )

    def test_auto_publish_cannot_enable(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][0]["auto_publish"] = "GO"
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("AUTO_PUBLISH" in e for e in grant_verify.verify(root)))

    def test_standing_permission_forbidden(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][0]["standing_permission"] = True
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("standing permission" in e for e in grant_verify.verify(root)))

    def test_base_agent_permission_remains_false(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][0]["base_agent_may_publish"] = True
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("base agent permission" in e for e in grant_verify.verify(root)))

    def test_account_identity_bound_to_linkedin_company(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][0]["account_identity"] = "company:999:wrong"
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("account identity" in e for e in grant_verify.verify(root)))

    def test_publication_decision_must_cover_grant(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_human_decision_observations_v1.json")
            obs = next(
                o
                for o in data["observations"]
                if o["decision_type"] == "AUTHORIZE_PUBLICATION"
            )
            obs["item_ids"] = ["W2-01"]
            save(root, "content_human_decision_observations_v1.json", data)
            self.assertTrue(
                any(
                    "does not cover all grant items" in e
                    for e in grant_verify.verify(root)
                )
            )

    def test_post_grant_observation_does_not_rewrite_issuance_scope(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            data["observations"] = [
                o
                for o in data["observations"]
                if not (o["item_id"] == "W1-01" and o["channel"] == "LinkedIn")
            ]
            data["coverage"]["logical_targets_observed"] = 7
            data["coverage"]["physical_remote_records"] = 9
            save(root, "content_publication_observations_v1.json", data)
            self.assertEqual(grant_verify.verify(root), [])

    def test_missing_target_outside_issuance_scope_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            data["observations"] = [
                o
                for o in data["observations"]
                if not (o["item_id"] == "W2-01" and o["channel"] == "LinkedIn")
            ]
            data["coverage"]["logical_targets_observed"] = 7
            data["coverage"]["physical_remote_records"] = 9
            save(root, "content_publication_observations_v1.json", data)
            self.assertTrue(
                any(
                    "outside immutable issuance scope" in e
                    for e in grant_verify.verify(root)
                )
            )

    def test_terminal_grant_cannot_execute(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][0]["scoped_agent_execution_authorized"] = True
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(
                any(
                    "terminal grant must not authorize execution" in e
                    for e in grant_verify.verify(root)
                )
            )

    def test_terminal_grant_requires_terminal_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][0].pop("status_reason")
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("status_reason" in e for e in grant_verify.verify(root)))

    def test_active_grant_requires_execution_true(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            grant = data["grants"][0]
            grant["status"] = "ACTIVE"
            grant["scoped_agent_execution_authorized"] = False
            grant.pop("status_changed_at", None)
            grant.pop("status_reason", None)
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(
                any(
                    "ACTIVE grant must authorize" in e
                    for e in grant_verify.verify(root)
                )
            )

    def test_active_scope_must_equal_current_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            grant = data["grants"][0]
            grant["status"] = "ACTIVE"
            grant["scoped_agent_execution_authorized"] = True
            grant.pop("status_changed_at", None)
            grant.pop("status_reason", None)
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(
                any(
                    "ACTIVE grant scope must equal exact current unobserved" in e
                    for e in grant_verify.verify(root)
                )
            )

    def test_expired_status_changed_at_cannot_predate_expiry(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][0]["status_changed_at"] = "2026-09-13T11:59:59-03:00"
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(
                any(
                    "status_changed_at cannot predate expires_at" in e
                    for e in grant_verify.verify(root)
                )
            )

    def test_consumed_requires_zero_current_missing_targets(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            grant = data["grants"][0]
            grant["status"] = "CONSUMED"
            grant["status_reason"] = "synthetic test"
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(
                any(
                    "CONSUMED grant requires zero current missing targets" in e
                    for e in grant_verify.verify(root)
                )
            )

    def test_policy_pins_issuance_state(self):
        policy = load(ROOT, "CONTENT_EXECUTION_GRANT_POLICY_V1.json")
        self.assertEqual(
            policy["grant_issuance_commit"],
            "cec887029a78974f23e530772e3bb46b2054ae02",
        )
        self.assertEqual(
            policy["grant_issuance_state_sha256"],
            "3484247f05ffede2bd463b4521d67b061781d5601b731f0fbc715e9049b82ba2",
        )

    def test_terminal_grant_preserves_issuance_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            grant = load(root, "content_execution_grants_v1.json")["grants"][0]
            self.assertEqual(
                grant["item_allowlist"],
                ["W1-01", "W1-02", "W1-03", "W2-02"],
            )
            self.assertEqual(grant["observed_logical_targets_before_grant"], 6)
            self.assertEqual(grant["remaining_logical_target_limit"], 4)
            self.assertEqual(
                grant["scope_sha256"],
                "33008bc179cc386de3881b2193b3f45bca80f89c749048a079d61e6a5ea73a37",
            )

    def test_issuance_snapshot_hash_rejects_counter_rewrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            grant = data["grants"][0]
            grant["observed_logical_targets_before_grant"] = 8
            grant["remaining_logical_target_limit"] = 2
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(
                any(
                    "issuance snapshot differs" in e
                    for e in grant_verify.verify(root)
                )
            )

    def test_required_git_read_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / ".git").mkdir()
            failed = SimpleNamespace(returncode=128, stdout="", stderr="fatal")
            with mock.patch.object(grant_verify.subprocess, "run", return_value=failed):
                with self.assertRaises(ValueError):
                    grant_verify._git_json(
                        root,
                        "deadbeef",
                        grant_verify.DECISIONS,
                        required=True,
                    )

    def test_optional_git_read_can_skip_missing_history(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / ".git").mkdir()
            failed = SimpleNamespace(returncode=128, stdout="", stderr="fatal")
            with mock.patch.object(grant_verify.subprocess, "run", return_value=failed):
                self.assertIsNone(
                    grant_verify._git_json(
                        root,
                        "HEAD^",
                        grant_verify.GRANTS,
                    )
                )


if __name__ == "__main__":
    unittest.main()
