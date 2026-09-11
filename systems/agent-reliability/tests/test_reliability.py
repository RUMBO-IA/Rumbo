from rumbo_reliability.engine import InMemoryResource, ReliabilityEngine
from rumbo_reliability.models import TaskRequest


def req(task_id="t1", value="updated", auth="allow", key="k1", revision=0):
    return TaskRequest(task_id, value, auth, key, revision)


def test_missing_authority_blocked():
    engine = ReliabilityEngine()
    result = engine.run(req(auth=None))
    assert result.authority == "FAIL"
    assert result.execution == "BLOCKED"
    assert result.final_state == "NOT_AUTHORIZED"
    assert engine.resource.value == "initial"


def test_valid_execution_verified():
    engine = ReliabilityEngine()
    result = engine.run(req())
    assert result.authority == "PASS"
    assert result.execution == "REPORTED_SUCCESS"
    assert result.verification == "PASS"
    assert result.final_state == "VERIFIED"
    assert engine.resource.value == "updated"


def test_false_success_not_proven():
    engine = ReliabilityEngine()

    def lying_executor(resource, intended):
        return True

    result = engine.run(req(), executor=lying_executor)
    assert result.execution == "REPORTED_SUCCESS"
    assert result.verification == "FAIL"
    assert result.final_state == "NOT_PROVEN"
    assert engine.resource.value == "initial"


def test_duplicate_retry_does_not_duplicate_side_effect():
    engine = ReliabilityEngine()
    calls = {"n": 0}

    def counting_executor(resource, intended):
        calls["n"] += 1
        resource.value = intended
        resource.revision += 1
        return True

    first = engine.run(req(), executor=counting_executor)
    second = engine.run(req(task_id="t2"), executor=counting_executor)
    assert first.final_state == "VERIFIED"
    assert second.execution == "DUPLICATE_BLOCKED"
    assert second.final_state == "VERIFIED"
    assert calls["n"] == 1


def test_stale_context_blocked():
    engine = ReliabilityEngine(InMemoryResource(value="current", revision=3))
    result = engine.run(req(revision=2))
    assert result.execution == "BLOCKED"
    assert result.final_state == "STALE_CONTEXT"
    assert engine.resource.value == "current"


def test_missing_verification_evidence_not_proven():
    engine = ReliabilityEngine()

    def no_evidence(resource, intended):
        return None

    result = engine.run(req(), verifier=no_evidence)
    assert result.verification == "MISSING_EVIDENCE"
    assert result.final_state == "NOT_PROVEN"


def test_verification_disagreement_not_proven():
    engine = ReliabilityEngine()

    def disagree(resource, intended):
        return False

    result = engine.run(req(), verifier=disagree)
    assert result.verification == "FAIL"
    assert result.final_state == "NOT_PROVEN"
