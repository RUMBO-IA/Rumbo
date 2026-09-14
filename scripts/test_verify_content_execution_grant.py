from __future__ import annotations

import json
import pathlib
import shutil
import tempfile
import unittest

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
    (root / "docs" / "brand" / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class ContentExecutionGrantTests(unittest.TestCase):
    def test_baseline_revoked_passes(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(grant_verify.verify(make_root(td)), [])

    def test_scope_cannot_expand(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][0]["item_allowlist"].append("W2-01")
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("exact unobserved" in e or "scope_sha256" in e for e in grant_verify.verify(root)))

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
            obs = next(o for o in data["observations"] if o["decision_type"] == "AUTHORIZE_PUBLICATION")
            obs["item_ids"] = ["W2-01"]
            save(root, "content_human_decision_observations_v1.json", data)
            self.assertTrue(any("does not cover all grant items" in e for e in grant_verify.verify(root)))

    def test_observation_change_recomputes_exact_missing_scope(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            data["observations"] = [o for o in data["observations"] if not (o["item_id"] == "W1-01" and o["channel"] == "LinkedIn")]
            data["coverage"]["logical_targets_observed"] = 7
            data["coverage"]["physical_remote_records"] = 9
            save(root, "content_publication_observations_v1.json", data)
            self.assertTrue(any("exact unobserved" in e or "observed logical target count" in e for e in grant_verify.verify(root)))

    def test_revoked_grant_cannot_execute(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            data["grants"][0]["scoped_agent_execution_authorized"] = True
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("terminal grant must not authorize execution" in e for e in grant_verify.verify(root)))

    def test_revoked_grant_requires_terminal_metadata(self):
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
            self.assertTrue(any("ACTIVE grant must authorize" in e for e in grant_verify.verify(root)))

    def test_consumed_requires_zero_missing_targets(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_execution_grants_v1.json")
            grant = data["grants"][0]
            grant["status"] = "CONSUMED"
            grant["item_allowlist"] = []
            grant["remaining_logical_target_limit"] = 0
            grant["scope_sha256"] = grant_verify._scope_sha(grant)
            grant["status_reason"] = "synthetic test"
            save(root, "content_execution_grants_v1.json", data)
            self.assertTrue(any("CONSUMED grant requires zero missing" in e for e in grant_verify.verify(root)))


if __name__ == "__main__":
    unittest.main()
