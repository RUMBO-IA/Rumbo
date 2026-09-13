from __future__ import annotations

import json
import pathlib
import shutil
import tempfile
import unittest

from scripts import verify_content_evidence_v2 as evidence

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = (
    "content_registry_v2.json", "distribution_lock_v1.json",
    "CONTENT_HUMAN_DECISION_OBSERVATION_SCHEMA_V1.json",
    "CONTENT_PUBLICATION_OBSERVATION_SCHEMA_V1.json",
    "CONTENT_PUBLICATION_RECEIPT_SCHEMA_V2.json",
    "content_human_decision_observations_v1.json",
    "content_publication_observations_v1.json",
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


class ContentEvidenceV2Tests(unittest.TestCase):
    def test_evidence_policy_must_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            path = root / "docs/brand/content_registry_v2.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["evidence_observation_policy"]["observations_promote_state"] = True
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self.assertTrue(any("evidence_observation_policy" in e for e in evidence.verify(root)))

    def test_baseline_passes(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(evidence.verify(make_root(td)), [])

    def test_decision_hash_must_be_sha256(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_human_decision_observations_v1.json")
            data["observations"][0]["decision_text_sha256"] = "bad"
            save(root, "content_human_decision_observations_v1.json", data)
            self.assertTrue(any("decision_text_sha256" in e for e in evidence.verify(root)))

    def test_unsigned_decision_cannot_claim_human_signed(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_human_decision_observations_v1.json")
            data["observations"][0]["proof_strength"] = "HUMAN_SIGNED"
            save(root, "content_human_decision_observations_v1.json", data)
            self.assertTrue(any("proof strength" in e for e in evidence.verify(root)))

    def test_observation_copy_hash_must_match_registry(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            data["observations"][0]["content_sha256"] = "0" * 64
            save(root, "content_publication_observations_v1.json", data)
            self.assertTrue(any("content_sha256 mismatch" in e for e in evidence.verify(root)))

    def test_observation_account_identity_must_match_distribution_lock(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            data["observations"][0]["account_identity"] = "handle:someone-else"
            save(root, "content_publication_observations_v1.json", data)
            self.assertTrue(any("account_identity mismatch" in e for e in evidence.verify(root)))

    def test_duplicate_remote_id_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            rid = data["observations"][0]["remote_records"][0]["remote_id"]
            data["observations"][1]["remote_records"][0]["remote_id"] = rid
            save(root, "content_publication_observations_v1.json", data)
            self.assertTrue(any("duplicate remote_id" in e for e in evidence.verify(root)))

    def test_missing_provider_job_id_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            data["observations"][0]["provider_job_id"] = ""
            save(root, "content_publication_observations_v1.json", data)
            self.assertTrue(any("provider_job_id" in e for e in evidence.verify(root)))

    def test_readback_cannot_precede_publish(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            rec = data["observations"][0]["remote_records"][0]
            rec["readback_at"] = "2026-09-12T20:00:00-03:00"
            save(root, "content_publication_observations_v1.json", data)
            self.assertTrue(any("readback precedes publish" in e for e in evidence.verify(root)))

    def test_observed_effect_cannot_self_promote(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            data["observations"][0]["canonical_promotion"] = "PASS"
            save(root, "content_publication_observations_v1.json", data)
            self.assertTrue(any("must not self-promote" in e for e in evidence.verify(root)))

    def test_multi_record_x_observation_is_supported(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            data = load(root, "content_publication_observations_v1.json")
            w102 = next(o for o in data["observations"] if o["item_id"] == "W1-02")
            self.assertEqual(len(w102["remote_records"]), 2)
            self.assertEqual(evidence.verify(root), [])


if __name__ == "__main__":
    unittest.main()
