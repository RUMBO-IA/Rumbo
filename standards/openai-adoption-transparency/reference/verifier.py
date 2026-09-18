#!/usr/bin/env python3
"""Verify an OpenAI Adoption Transparency Protocol v1 envelope."""
import argparse
import base64
import hashlib
import json
from datetime import datetime

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError as exc:
    raise SystemExit("cryptography is required: pip install cryptography") from exc

PROTECTED = {"installations_total", "installations_new", "uninstallations", "active_users_7d", "active_users_30d", "retention_30d"}

def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

def parse_dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def verify(envelope, public_key_hex):
    assert isinstance(envelope, dict)
    payload = envelope["payload"]
    att = envelope["attestation"]
    assert payload["schema"] == "rumbo.openai-adoption-transparency/report-v1"
    assert payload["protocol_version"] == "1.0"
    assert isinstance(payload["report_revision"], int) and payload["report_revision"] >= 1
    assert payload["source"] == "openai"
    assert isinstance(payload["publisher_id"], str) and payload["publisher_id"]
    assert isinstance(payload["app_id"], str) and payload["app_id"]
    period = payload["reporting_period"]
    start, end = parse_dt(period["from"]), parse_dt(period["to"])
    assert start < end
    assert parse_dt(payload["generated_at"]) >= end
    privacy = payload["privacy"]
    assert privacy["user_level_data_exported"] is False
    minimum = privacy["minimum_unique_user_cohort"]
    assert minimum >= 2
    metrics = payload["metrics"]
    for name, metric in metrics.items():
        assert metric["status"] in {"exact", "suppressed"}
        if metric["status"] == "exact":
            assert "value" in metric and metric["value"] >= 0
            if name in PROTECTED and isinstance(metric["value"], int):
                assert metric["value"] >= minimum, f"{name} must be suppressed below cohort threshold"
        else:
            assert "reason" in metric and "value" not in metric
    assert att["issuer"] == "openai"
    assert att["algorithm"] == "Ed25519"
    digest = hashlib.sha256(canonical_json(payload)).hexdigest()
    assert digest == att["payload_sha256"], "payload_sha256 mismatch"
    signature = base64.b64decode(att["signature"], validate=True)
    public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
    public_key.verify(signature, canonical_json(payload))
    return digest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    parser.add_argument("--public-key-hex", required=True)
    args = parser.parse_args()
    report = json.loads(open(args.report, encoding="utf-8").read())
    digest = verify(report, args.public_key_hex)
    print("PASS: signature, hash, schema semantics, chronology, and privacy rules verified")
    print("payload_sha256 =", digest)

if __name__ == "__main__":
    main()
