from __future__ import annotations

import json
import pathlib
import shutil
import tempfile
import unittest

from scripts import verify_content_contract as content

ROOT = pathlib.Path(__file__).resolve().parents[1]


def make_root(tmp: str) -> pathlib.Path:
    root = pathlib.Path(tmp)
    brand = root / "docs" / "brand"
    brand.mkdir(parents=True)
    for name in ("content_registry_v2.json", "identity_registry_v1.json", "distribution_lock_v1.json", "CONTENT_CANON_V2.md"):
        shutil.copy2(ROOT / "docs" / "brand" / name, brand / name)
    return root


def load_registry(root: pathlib.Path) -> dict:
    path = root / "docs" / "brand" / "content_registry_v2.json"
    return json.loads(path.read_text(encoding="utf-8"))


def save_registry(root: pathlib.Path, data: dict) -> None:
    path = root / "docs" / "brand" / "content_registry_v2.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class ContentContractTests(unittest.TestCase):
    def test_baseline_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            self.assertEqual(content.verify(root), [])

    def test_auto_publish_must_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            data["auto_publish"] = "PASS"
            save_registry(root, data)
            self.assertTrue(any("AUTO_PUBLISH" in e for e in content.verify(root)))

    def test_unknown_rumbo_identity_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            data["items"][0]["identity"] = "NEXO 3.0"
            save_registry(root, data)
            errors = content.verify(root)
            self.assertTrue(any("identity" in e for e in errors))

    def test_denied_legacy_copy_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            data["items"][0]["copy"] += " 3x más leads"
            save_registry(root, data)
            self.assertTrue(any("denied" in e for e in content.verify(root)))

    def test_measured_claim_requires_receipt_before_release(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["claim_class"] = "MEASURED"
            item["publication_state"] = "READY_FOR_HUMAN_REVIEW"
            item.pop("metric_receipt", None)
            save_registry(root, data)
            self.assertTrue(any("metric_receipt" in e for e in content.verify(root)))

    def test_published_requires_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            data["items"][0]["publication_state"] = "PUBLISHED"
            data["items"][0]["publication_receipt"] = None
            save_registry(root, data)
            self.assertTrue(any("publication_receipt" in e for e in content.verify(root)))

    def test_release_state_requires_distribution_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            data["items"][0]["publication_state"] = "READY_FOR_HUMAN_REVIEW"
            save_registry(root, data)
            lock_path = root / "docs" / "brand" / "distribution_lock_v1.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8-sig"))
            lock["overall_status"] = "PARTIAL_PASS"
            lock_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")
            self.assertTrue(any("DISTRIBUTION=PASS" in e for e in content.verify(root)))

    def test_personal_lane_cannot_inherit_rumbo_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            data["items"][0]["lane"] = "PERSONAL_BRAND"
            save_registry(root, data)
            self.assertTrue(any("personal lane" in e for e in content.verify(root)))


if __name__ == "__main__":
    unittest.main()
