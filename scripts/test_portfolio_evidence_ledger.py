import tempfile
import unittest
from pathlib import Path

import portfolio_evidence_ledger as ledger


def record(**overrides):
    base = {
        "record_id": "rec-001",
        "timestamp": "2026-09-08T08:00:00Z",
        "lane_id": "agent-reliability",
        "artifact_id": "rm-004",
        "artifact_version": "0.1.6",
        "claim": "bounded case study is verified",
        "epistemic_status": "EVIDENCE",
        "maturity_status": "VERIFIED",
        "source_type": "github_pr",
        "source_locator": "RUMBO-IA/Rumbo#62",
        "content_sha256": "a" * 64,
        "parent_record_id": None,
        "supersedes": [],
        "tests": {"passed": 89, "failed": 0},
        "authority": {"granted": False, "scope": None},
        "production_status": "NO_GO",
        "blocker": None,
        "falsification_attempt": "canonical Git blob comparison",
        "result": "PASS",
    }
    base.update(overrides)
    return base


class PortfolioEvidenceLedgerTests(unittest.TestCase):
    def test_digest_stable(self):
        first = record()
        second = dict(reversed(list(first.items())))
        self.assertEqual(ledger.record_digest(first), ledger.record_digest(second))

    def test_append_is_idempotent_for_exact_same_record(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            self.assertEqual(ledger.append_record(path, record()), "APPENDED")
            self.assertEqual(ledger.append_record(path, record()), "ALREADY_PRESENT")
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 1)

    def test_record_id_collision_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "ledger.jsonl"
            ledger.append_record(path, record())
            changed = record(claim="different claim")
            with self.assertRaisesRegex(ValueError, "RECORD_ID_COLLISION"):
                ledger.append_record(path, changed)

    def test_production_go_requires_explicit_authority_and_verified_maturity(self):
        with self.assertRaisesRegex(ValueError, "PRODUCTION_AUTHORITY_REQUIRED"):
            ledger.validate_record(record(production_status="GO"))
        with self.assertRaisesRegex(ValueError, "PRODUCTION_MATURITY_REQUIRED"):
            ledger.validate_record(record(production_status="GO", maturity_status="TESTED", authority={"granted": True, "scope": "production"}))

    def test_reducer_uses_supersession_then_timestamp_deterministically(self):
        old = record(record_id="rec-old", timestamp="2026-09-08T08:00:00Z", result="PARTIAL")
        newer = record(record_id="rec-new", timestamp="2026-09-08T09:00:00Z", supersedes=["rec-old"], result="PASS")
        unrelated = record(record_id="rec-other", artifact_id="safe-merge", timestamp="2026-09-08T07:00:00Z")
        current = ledger.reduce_current([newer, unrelated, old])
        self.assertEqual(current[("agent-reliability", "rm-004")]["record_id"], "rec-new")
        self.assertEqual(current[("agent-reliability", "safe-merge")]["record_id"], "rec-other")

    def test_reducer_rejects_dangling_supersedes(self):
        bad = record(supersedes=["missing-record"])
        with self.assertRaisesRegex(ValueError, "DANGLING_SUPERSEDES"):
            ledger.reduce_current([bad])


if __name__ == "__main__":
    unittest.main()
