from __future__ import annotations

import hashlib
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
    for name in ("content_registry_v2.json", "identity_registry_v1.json", "distribution_lock_v1.json", "CONTENT_CANON_V2.md", "CHANNEL_MATRIX_V1.md", "CONTENT_REVIEW_PACKET_V1.md", "CONTENT_APPROVAL_RECEIPT_SCHEMA_V1.json", "CONTENT_PUBLICATION_RECEIPT_SCHEMA_V1.json", "CONTENT_PUBLICATION_AUTHORIZATION_RECEIPT_SCHEMA_V1.json"):
        shutil.copy2(ROOT / "docs" / "brand" / name, brand / name)
    shutil.copytree(ROOT / "docs" / "brand" / "content_approval_receipts", brand / "content_approval_receipts", dirs_exist_ok=True)
    return root


def load_registry(root: pathlib.Path) -> dict:
    path = root / "docs" / "brand" / "content_registry_v2.json"
    return json.loads(path.read_text(encoding="utf-8"))


def save_registry(root: pathlib.Path, data: dict) -> None:
    path = root / "docs" / "brand" / "content_registry_v2.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def attach_valid_approval_receipt(root: pathlib.Path, item: dict, *, content_sha256: str | None = None) -> None:
    rel = pathlib.Path("docs/brand/content_approval_receipts") / f"{item['id']}.json"
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": 1,
        "item_id": item["id"],
        "decision": "APPROVED",
        "content_sha256": content_sha256 or hashlib.sha256(item["copy"].encode("utf-8")).hexdigest(),
        "review_packet_ref": item["review_packet_ref"],
        "target_channels": item["target_channels"],
        "reviewer": "human-reviewer",
        "reviewed_at": "2026-09-12T19:40:00Z",
        "source": "explicit_human_approval",
    }
    path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    item["approval_receipt_ref"] = rel.as_posix()


def attach_valid_publication_authorization_receipt(root: pathlib.Path, item: dict, *, content_sha256: str | None = None) -> None:
    rel = pathlib.Path("docs/brand/content_publication_authorization_receipts") / f"{item['id']}.json"
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": 1,
        "item_id": item["id"],
        "decision": "AUTHORIZE_PUBLICATION",
        "content_sha256": content_sha256 or hashlib.sha256(item["copy"].encode("utf-8")).hexdigest(),
        "approval_receipt_ref": item["approval_receipt_ref"],
        "target_channels": item["target_channels"],
        "authorizer": "human-authorizer",
        "authorized_at": "2026-09-12T19:50:00Z",
        "source": "explicit_human_publication_authorization",
    }
    path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    item["publication_authorization_receipt_ref"] = rel.as_posix()


def attach_valid_publication_receipt(root: pathlib.Path, item: dict, *, content_sha256: str | None = None, readback_status: str = "PASS", channels: list[str] | None = None) -> None:
    if not item.get("publication_authorization_receipt_ref"):
        attach_valid_publication_authorization_receipt(root, item)
    rel = pathlib.Path("docs/brand/content_publication_receipts") / f"{item['id']}.json"
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    selected = channels or item["target_channels"]
    receipt = {
        "schema_version": 1,
        "item_id": item["id"],
        "status": "PUBLISHED",
        "content_sha256": content_sha256 or hashlib.sha256(item["copy"].encode("utf-8")).hexdigest(),
        "distribution_lock_sha256": content._distribution_lock_sha256(root),
        "approval_receipt_ref": item["approval_receipt_ref"],
        "publication_authorization_receipt_ref": item["publication_authorization_receipt_ref"],
        "review_packet_ref": item["review_packet_ref"],
        "target_channels": item["target_channels"],
        "publications": [
            {
                "channel": channel,
                "account_identity": ("company:145014017:rumbo-ia" if channel == "LinkedIn" else "handle:RumboAGI"),
                "remote_url": (f"https://www.linkedin.com/feed/update/{item['id']}" if channel == "LinkedIn" else f"https://x.com/RumboAGI/status/{item['id']}"),
                "remote_id": f"remote-{channel.lower()}-{item['id']}",
                "published_at": "2026-09-12T20:00:00Z",
                "readback_at": "2026-09-12T20:01:00Z",
                "readback_status": readback_status,
                "account_binding_ref": "docs/brand/distribution_lock_v1.json",
            } for channel in selected
        ],
        "publisher": "authenticated-human-operator",
        "source": "authenticated_publication_action",
    }
    path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    item["publication_receipt"] = rel.as_posix()


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

    def test_releaseable_state_requires_nonempty_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            data["items"][0]["copy"] = ""
            save_registry(root, data)
            self.assertTrue(any("non-empty copy" in e for e in content.verify(root)))

    def test_demo_releaseable_copy_requires_visible_label(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["claim_class"] = "DEMO"
            item["copy"] = "Una IA puede proponer un rango de precio usando supuestos expl?citos."
            save_registry(root, data)
            self.assertTrue(any("visible demo/example label" in e for e in content.verify(root)))

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

    def test_malformed_distribution_lock_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            lock_path = root / "docs" / "brand" / "distribution_lock_v1.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8-sig"))
            lock["schema_version"] = 999
            lock_path.write_text(json.dumps(lock, indent=2), encoding="utf-8")
            self.assertTrue(any("distribution authority invalid" in e for e in content.verify(root)))

    def test_review_ready_requires_review_packet_ref(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "READY_FOR_HUMAN_REVIEW"
            item.pop("review_packet_ref", None)
            save_registry(root, data)
            self.assertTrue(any("review_packet_ref" in e for e in content.verify(root)))

    def test_review_ready_rejects_unknown_target_channel(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "READY_FOR_HUMAN_REVIEW"
            item["review_packet_ref"] = "docs/brand/CONTENT_REVIEW_PACKET_V1.md"
            item["target_channels"] = ["UnknownChannel"]
            save_registry(root, data)
            self.assertTrue(any("target channel" in e for e in content.verify(root)))

    def test_approved_requires_approval_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "APPROVED"
            item.pop("approval_receipt_ref", None)
            save_registry(root, data)
            self.assertTrue(any("approval_receipt_ref" in e for e in content.verify(root)))

    def test_approved_rejects_copy_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "APPROVED"
            attach_valid_approval_receipt(root, item, content_sha256="0" * 64)
            save_registry(root, data)
            self.assertTrue(any("content_sha256 mismatch" in e for e in content.verify(root)))

    def test_valid_approved_receipt_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "APPROVED"
            attach_valid_approval_receipt(root, item)
            save_registry(root, data)
            self.assertEqual(content.verify(root), [])

    def test_published_cannot_skip_approval_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            item["publication_receipt"] = "authenticated-publication-receipt"
            item.pop("approval_receipt_ref", None)
            save_registry(root, data)
            self.assertTrue(any("approval_receipt_ref" in e for e in content.verify(root)))

    def test_approval_policy_forbids_agent_issuance(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            data["approval_policy"]["agent_may_issue_receipts"] = True
            save_registry(root, data)
            self.assertTrue(any("approval_policy" in e for e in content.verify(root)))

    def test_approved_rejects_nonhuman_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "APPROVED"
            attach_valid_approval_receipt(root, item)
            receipt_path = root / item["approval_receipt_ref"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["source"] = "agent_generated"
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("source must be explicit_human_approval" in e for e in content.verify(root)))

    def test_published_rejects_plain_string_publication_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            item["publication_receipt"] = "authenticated-publication-receipt"
            save_registry(root, data)
            self.assertTrue(any("JSON file under" in e for e in content.verify(root)))

    def test_valid_published_receipt_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            save_registry(root, data)
            self.assertEqual(content.verify(root), [])

    def test_published_rejects_content_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item, content_sha256="0" * 64)
            save_registry(root, data)
            self.assertTrue(any("publication receipt content_sha256 mismatch" in e for e in content.verify(root)))

    def test_published_requires_all_target_channels(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item, channels=[item["target_channels"][0]])
            save_registry(root, data)
            self.assertTrue(any("must match target_channels exactly" in e for e in content.verify(root)))

    def test_published_requires_readback_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item, readback_status="PENDING")
            save_registry(root, data)
            self.assertTrue(any("readback_status must be PASS" in e for e in content.verify(root)))

    def test_publication_policy_forbids_agent_publish(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            data["publication_policy"]["agent_may_publish"] = True
            save_registry(root, data)
            self.assertTrue(any("publication_policy" in e for e in content.verify(root)))

    def test_published_rejects_approval_ref_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            receipt_path = root / item["publication_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["approval_receipt_ref"] = "docs/brand/content_approval_receipts/OTHER.json"
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("approval_receipt_ref mismatch" in e for e in content.verify(root)))

    def test_published_rejects_wrong_remote_host(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            receipt_path = root / item["publication_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["publications"][0]["remote_url"] = "https://example.com/fake"
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("remote_url host mismatch" in e for e in content.verify(root)))

    def test_published_rejects_binding_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            receipt_path = root / item["publication_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["publications"][0]["account_binding_ref"] = "wrong.json"
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("account_binding_ref mismatch" in e for e in content.verify(root)))

    def test_published_rejects_unauthenticated_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            receipt_path = root / item["publication_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["source"] = "agent_generated"
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("source must be authenticated_publication_action" in e for e in content.verify(root)))

    def test_published_rejects_distribution_lock_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            receipt_path = root / item["publication_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["distribution_lock_sha256"] = "0" * 64
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("distribution_lock_sha256 mismatch" in e for e in content.verify(root)))

    def test_published_rejects_account_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            receipt_path = root / item["publication_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["publications"][0]["account_identity"] = "company:999:wrong"
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("account_identity mismatch" in e for e in content.verify(root)))

    def test_published_rejects_wrong_x_handle_url(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            receipt_path = root / item["publication_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            x_pub = next(pub for pub in receipt["publications"] if pub["channel"] == "X")
            x_pub["remote_url"] = f"https://x.com/OtherHandle/status/{item['id']}"
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("canonical handle" in e for e in content.verify(root)))

    def test_published_rejects_extra_receipt_field(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            receipt_path = root / item["publication_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["unexpected"] = "x"
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("unsupported fields" in e for e in content.verify(root)))

    def test_published_rejects_extra_publication_field(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            receipt_path = root / item["publication_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["publications"][0]["unexpected"] = "x"
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("publication entry contains unsupported fields" in e for e in content.verify(root)))

    def test_published_malformed_target_channels_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            item = data["items"][0]
            item["publication_state"] = "PUBLISHED"
            attach_valid_approval_receipt(root, item)
            attach_valid_publication_receipt(root, item)
            receipt_path = root / item["publication_receipt"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["target_channels"] = None
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            save_registry(root, data)
            self.assertTrue(any("target_channels mismatch" in e for e in content.verify(root)))


    def test_published_requires_publication_authorization_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td); data = load_registry(root); item = data["items"][0]
            item["publication_state"] = "PUBLISHED"; attach_valid_approval_receipt(root, item); attach_valid_publication_receipt(root, item)
            item.pop("publication_authorization_receipt_ref", None); save_registry(root, data)
            self.assertTrue(any("publication_authorization_receipt_ref" in e for e in content.verify(root)))

    def test_publication_authorization_rejects_content_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td); data = load_registry(root); item = data["items"][0]
            item["publication_state"] = "PUBLISHED"; attach_valid_approval_receipt(root, item)
            attach_valid_publication_authorization_receipt(root, item, content_sha256="0" * 64); attach_valid_publication_receipt(root, item); save_registry(root, data)
            self.assertTrue(any("publication authorization content_sha256 mismatch" in e for e in content.verify(root)))

    def test_publication_authorization_rejects_nonhuman_source(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td); data = load_registry(root); item = data["items"][0]
            item["publication_state"] = "PUBLISHED"; attach_valid_approval_receipt(root, item); attach_valid_publication_authorization_receipt(root, item); attach_valid_publication_receipt(root, item)
            p = root / item["publication_authorization_receipt_ref"]; r = json.loads(p.read_text(encoding="utf-8")); r["source"] = "agent_generated"; p.write_text(json.dumps(r, indent=2), encoding="utf-8"); save_registry(root, data)
            self.assertTrue(any("explicit_human_publication_authorization" in e for e in content.verify(root)))


    def test_publication_receipt_rejects_authorization_ref_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td); data = load_registry(root); item = data["items"][0]
            item["publication_state"] = "PUBLISHED"; attach_valid_approval_receipt(root, item); attach_valid_publication_receipt(root, item)
            p = root / item["publication_receipt"]; r = json.loads(p.read_text(encoding="utf-8")); r["publication_authorization_receipt_ref"] = "docs/brand/content_publication_authorization_receipts/OTHER.json"; p.write_text(json.dumps(r, indent=2), encoding="utf-8"); save_registry(root, data)
            self.assertTrue(any("publication_authorization_receipt_ref mismatch" in e for e in content.verify(root)))

    def test_distribution_lock_hash_is_canonical_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td); data = load_registry(root); item = data["items"][0]
            item["publication_state"] = "PUBLISHED"; attach_valid_approval_receipt(root, item); attach_valid_publication_receipt(root, item); save_registry(root, data)
            lock_p = root / "docs/brand/distribution_lock_v1.json"; lock = json.loads(lock_p.read_text(encoding="utf-8-sig")); lock_p.write_text(json.dumps(lock, ensure_ascii=False, indent=7, sort_keys=True), encoding="utf-8")
            self.assertEqual(content.verify(root), [])


    def test_approval_receipt_malformed_target_channels_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td); data = load_registry(root); item = data["items"][0]
            item["publication_state"] = "APPROVED"; attach_valid_approval_receipt(root, item)
            p = root / item["approval_receipt_ref"]; r = json.loads(p.read_text(encoding="utf-8")); r["target_channels"] = [{}]; p.write_text(json.dumps(r), encoding="utf-8"); save_registry(root, data)
            self.assertTrue(any("approval receipt target_channels mismatch" in e for e in content.verify(root)))

    def test_publication_authorization_malformed_target_channels_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td); data = load_registry(root); item = data["items"][0]
            item["publication_state"] = "PUBLISHED"; attach_valid_approval_receipt(root, item); attach_valid_publication_receipt(root, item)
            p = root / item["publication_authorization_receipt_ref"]; r = json.loads(p.read_text(encoding="utf-8")); r["target_channels"] = [{}]; p.write_text(json.dumps(r), encoding="utf-8"); save_registry(root, data)
            self.assertTrue(any("publication authorization target_channels mismatch" in e for e in content.verify(root)))

    def test_personal_lane_cannot_inherit_rumbo_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load_registry(root)
            data["items"][0]["lane"] = "PERSONAL_BRAND"
            save_registry(root, data)
            self.assertTrue(any("personal lane" in e for e in content.verify(root)))


if __name__ == "__main__":
    unittest.main()
