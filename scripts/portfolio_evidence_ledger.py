from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

REQUIRED_FIELDS = {"record_id", "timestamp", "lane_id", "artifact_id", "artifact_version", "claim", "epistemic_status", "maturity_status", "source_type", "source_locator", "content_sha256", "parent_record_id", "supersedes", "tests", "authority", "production_status", "blocker", "falsification_attempt", "result"}
EPISTEMIC_STATUSES = {"FACT", "EVIDENCE", "INFERENCE", "HYPOTHESIS", "PENDING"}
MATURITY_ORDER = {"IDEA": 0, "SPEC": 1, "DESIGNED": 2, "IMPLEMENTED": 3, "TESTED": 4, "VERIFIED": 5, "MERGED": 6, "RELEASED": 7}
PRODUCTION_STATUSES = {"NO_GO", "GO"}
RESULT_STATUSES = {"PASS", "PARTIAL", "FAIL", "BLOCKED", "NOT_PROVEN"}


def canonical_payload(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def record_digest(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_payload(record)).hexdigest()


def validate_record(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        raise ValueError(f"MISSING_FIELDS:{','.join(missing)}")
    if record["epistemic_status"] not in EPISTEMIC_STATUSES:
        raise ValueError("INVALID_EPISTEMIC_STATUS")
    if record["maturity_status"] not in MATURITY_ORDER:
        raise ValueError("INVALID_MATURITY_STATUS")
    if record["production_status"] not in PRODUCTION_STATUSES:
        raise ValueError("INVALID_PRODUCTION_STATUS")
    if record["result"] not in RESULT_STATUSES:
        raise ValueError("INVALID_RESULT")
    digest = record["content_sha256"]
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("INVALID_CONTENT_SHA256")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError("INVALID_CONTENT_SHA256") from exc
    supersedes = record["supersedes"]
    if not isinstance(supersedes, list) or not all(isinstance(item, str) and item for item in supersedes):
        raise ValueError("INVALID_SUPERSEDES")
    authority = record["authority"]
    if not isinstance(authority, dict) or not isinstance(authority.get("granted"), bool):
        raise ValueError("INVALID_AUTHORITY")
    if record["production_status"] == "GO":
        if authority.get("granted") is not True or not authority.get("scope"):
            raise ValueError("PRODUCTION_AUTHORITY_REQUIRED")
        if MATURITY_ORDER[record["maturity_status"]] < MATURITY_ORDER["VERIFIED"]:
            raise ValueError("PRODUCTION_MATURITY_REQUIRED")


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"INVALID_JSONL:{line_number}") from exc
        validate_record(record)
        records.append(record)
    return records


def append_record(path: Path, record: dict[str, Any]) -> str:
    validate_record(record)
    existing = load_records(path)
    for current in existing:
        if current["record_id"] != record["record_id"]:
            continue
        if record_digest(current) == record_digest(record):
            return "ALREADY_PRESENT"
        raise ValueError(f"RECORD_ID_COLLISION:{record['record_id']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_payload(record).decode("utf-8") + "\n")
    return "APPENDED"


def reduce_current(records: Iterable[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    items = list(records)
    by_id: dict[str, dict[str, Any]] = {}
    for record in items:
        validate_record(record)
        record_id = record["record_id"]
        previous = by_id.get(record_id)
        if previous is not None and record_digest(previous) != record_digest(record):
            raise ValueError(f"RECORD_ID_COLLISION:{record_id}")
        by_id[record_id] = record
    superseded: set[str] = set()
    for record in by_id.values():
        for target in record["supersedes"]:
            if target not in by_id:
                raise ValueError(f"DANGLING_SUPERSEDES:{target}")
            if (by_id[target]["lane_id"], by_id[target]["artifact_id"]) != (record["lane_id"], record["artifact_id"]):
                raise ValueError(f"CROSS_ARTIFACT_SUPERSESSION:{target}")
            superseded.add(target)
    current: dict[tuple[str, str], dict[str, Any]] = {}
    for record in by_id.values():
        if record["record_id"] in superseded:
            continue
        key = (record["lane_id"], record["artifact_id"])
        incumbent = current.get(key)
        if incumbent is None or (record["timestamp"], record["record_id"]) > (incumbent["timestamp"], incumbent["record_id"]):
            current[key] = record
    return current
