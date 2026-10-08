import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "openai-publication" / "agent-reliability" / "ADOPTION_OBSERVABILITY_AUDIT_2026-09-18.json"

record = json.loads(AUDIT.read_text(encoding="utf-8"))

required = {"schema", "observed_at", "subject", "findings", "evidence", "conclusion", "safe_next_measurement", "integrity_rule"}
missing = required - record.keys()
if missing:
    raise SystemExit(f"FAIL missing fields: {sorted(missing)}")

findings = record["findings"]
assert findings["openai_publisher_install_count"] in {"NOT_OBSERVABLE", "OBSERVED"}
assert findings["openai_publisher_active_user_count"] in {"NOT_OBSERVABLE", "OBSERVED"}
assert findings["self_measurement_for_current_package"] == "NOT_AVAILABLE_SKILLS_ONLY"

if findings["openai_publisher_install_count"] == "NOT_OBSERVABLE":
    assert "install_count" not in record
    assert "downloads" not in record

print("PASS: adoption observability audit is explicit, non-inferential, and bounded.")
print("install_count =", findings["openai_publisher_install_count"])
print("active_user_count =", findings["openai_publisher_active_user_count"])
print("self_measurement =", findings["self_measurement_for_current_package"])
