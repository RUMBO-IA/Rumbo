import base64, copy, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verifier import canonical_json, verify

def make_payload():
    return {
        "schema": "rumbo.openai-adoption-transparency/report-v1",
        "protocol_version": "1.0",
        "report_revision": 1,
        "source": "openai",
        "publisher_id": "pub_rumbo",
        "app_id": "app_rumbo_agent_reliability",
        "app_version": "0.1.6",
        "reporting_period": {"from": "2026-09-01T00:00:00Z", "to": "2026-09-18T00:00:00Z"},
        "generated_at": "2026-09-18T13:00:00Z",
        "privacy": {"user_level_data_exported": False, "minimum_unique_user_cohort": 5},
        "metrics": {
            "listing_impressions": {"status": "exact", "value": 1200},
            "installations_total": {"status": "exact", "value": 250},
            "installations_new": {"status": "exact", "value": 25},
            "uninstallations": {"status": "exact", "value": 8},
            "active_users_7d": {"status": "exact", "value": 12},
            "active_users_30d": {"status": "exact", "value": 31},
            "tool_calls_total": {"status": "exact", "value": 450},
            "retention_30d": {"status": "exact", "value": 0.42}
        }
    }

def make_envelope(private, payload=None):
    payload = payload or make_payload()
    raw = canonical_json(payload)
    signature = private.sign(raw)
    return {"payload": payload, "attestation": {
        "issuer": "openai",
        "key_id": "test-key-1",
        "algorithm": "Ed25519",
        "payload_sha256": hashlib.sha256(raw).hexdigest(),
        "signature": base64.b64encode(signature).decode("ascii")
    }}

def main():
    private = Ed25519PrivateKey.generate()
    public_hex = private.public_key().public_bytes_raw().hex()
    report = make_envelope(private)
    verify(report, public_hex)
    print("PASS valid envelope")

    opaque_id = copy.deepcopy(report)
    opaque_id["payload"]["app_id"] = "plugin_asdk_app_6a9b9c5f7a708191a145dddc5734dff2"
    raw = canonical_json(opaque_id["payload"])
    opaque_id["attestation"]["payload_sha256"] = hashlib.sha256(raw).hexdigest()
    opaque_id["attestation"]["signature"] = base64.b64encode(private.sign(raw)).decode("ascii")
    verify(opaque_id, public_hex)
    print("PASS opaque platform app id")

    tampered = copy.deepcopy(report)
    tampered["payload"]["metrics"]["tool_calls_total"]["value"] = 451
    try:
        verify(tampered, public_hex)
    except AssertionError:
        print("PASS tamper detected")
    else:
        raise AssertionError("tampering was not detected")

    suppressed = copy.deepcopy(report)
    suppressed["payload"]["metrics"]["active_users_7d"] = {"status": "suppressed", "reason": "cohort below threshold"}
    raw = canonical_json(suppressed["payload"])
    suppressed["attestation"]["payload_sha256"] = hashlib.sha256(raw).hexdigest()
    suppressed["attestation"]["signature"] = base64.b64encode(private.sign(raw)).decode("ascii")
    verify(suppressed, public_hex)
    print("PASS privacy suppression")

    bad = copy.deepcopy(report)
    bad["payload"]["metrics"]["active_users_7d"] = {"status": "exact", "value": 4}
    raw = canonical_json(bad["payload"])
    bad["attestation"]["payload_sha256"] = hashlib.sha256(raw).hexdigest()
    bad["attestation"]["signature"] = base64.b64encode(private.sign(raw)).decode("ascii")
    try:
        verify(bad, public_hex)
    except AssertionError:
        print("PASS small-cohort fail-closed")
    else:
        raise AssertionError("small cohort was accepted")

    wrong_issuer = copy.deepcopy(report)
    wrong_issuer["attestation"]["issuer"] = "attacker"
    try:
        verify(wrong_issuer, public_hex)
    except AssertionError:
        print("PASS wrong issuer rejected")
    else:
        raise AssertionError("wrong issuer was accepted")

    bad_time = copy.deepcopy(report)
    bad_time["payload"]["generated_at"] = "2026-09-17T13:00:00Z"
    raw = canonical_json(bad_time["payload"])
    bad_time["attestation"]["payload_sha256"] = hashlib.sha256(raw).hexdigest()
    bad_time["attestation"]["signature"] = base64.b64encode(private.sign(raw)).decode("ascii")
    try:
        verify(bad_time, public_hex)
    except AssertionError:
        print("PASS chronology rejected")
    else:
        raise AssertionError("invalid chronology was accepted")

    vector = json.loads((Path(__file__).with_name("test-vector.json")).read_text(encoding="utf-8"))
    digest = verify(vector["report"], vector["public_key_hex"])
    assert digest == vector["report"]["attestation"]["payload_sha256"]
    print("PASS published test vector")

if __name__ == "__main__":
    main()
