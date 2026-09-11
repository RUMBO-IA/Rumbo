from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from .models import TaskRequest, TaskResult


@dataclass
class InMemoryResource:
    value: str = "initial"
    revision: int = 0


@dataclass
class EvidenceLedger:
    entries: list[dict] = field(default_factory=list)

    def append(self, **entry: object) -> None:
        self.entries.append(dict(entry))


class ReliabilityEngine:
    """Minimal deterministic reference implementation for RUMBO reliability invariants."""

    VALID_AUTHORITY = "allow"

    def __init__(self, resource: Optional[InMemoryResource] = None) -> None:
        self.resource = resource or InMemoryResource()
        self.ledger = EvidenceLedger()
        self._idempotency: Dict[str, TaskResult] = {}

    def run(
        self,
        request: TaskRequest,
        *,
        executor: Optional[Callable[[InMemoryResource, str], bool]] = None,
        verifier: Optional[Callable[[InMemoryResource, str], Optional[bool]]] = None,
    ) -> TaskResult:
        capability = "PASS"

        # Retry deduplication is checked before stale-context rejection. A legitimate
        # retry may carry the revision observed before its already-completed side effect.
        # The idempotency record is therefore the authoritative evidence for this path.
        if request.idempotency_key in self._idempotency:
            prior = self._idempotency[request.idempotency_key]
            self.ledger.append(task_id=request.task_id, event="duplicate_retry", result="reused")
            return TaskResult(
                request.task_id,
                capability,
                prior.authority,
                "DUPLICATE_BLOCKED",
                prior.verification,
                prior.final_state,
                "existing idempotency key reused; no second side effect",
            )

        if request.revision < self.resource.revision:
            result = TaskResult(
                request.task_id,
                capability,
                "NOT_EVALUATED",
                "BLOCKED",
                "NOT_RUN",
                "STALE_CONTEXT",
                f"incoming_revision={request.revision}; canonical_revision={self.resource.revision}",
            )
            self.ledger.append(task_id=request.task_id, event="stale_context", result="blocked")
            return result

        if request.authority_token != self.VALID_AUTHORITY:
            result = TaskResult(
                request.task_id,
                capability,
                "FAIL",
                "BLOCKED",
                "NOT_RUN",
                "NOT_AUTHORIZED",
                "valid authority token missing",
            )
            self.ledger.append(task_id=request.task_id, event="authority", result="fail")
            return result

        self.ledger.append(task_id=request.task_id, event="authority", result="pass")

        executor = executor or self._default_executor
        reported_success = bool(executor(self.resource, request.intended_value))
        execution = "REPORTED_SUCCESS" if reported_success else "FAIL"
        self.ledger.append(task_id=request.task_id, event="execution", result=execution)

        if not reported_success:
            result = TaskResult(
                request.task_id,
                capability,
                "PASS",
                execution,
                "NOT_RUN",
                "EXECUTION_FAILED",
            )
            self._idempotency[request.idempotency_key] = result
            return result

        verifier = verifier or self._default_verifier
        verification_result = verifier(self.resource, request.intended_value)

        if verification_result is None:
            verification = "MISSING_EVIDENCE"
            final_state = "NOT_PROVEN"
        elif verification_result is True:
            verification = "PASS"
            final_state = "VERIFIED"
        else:
            verification = "FAIL"
            final_state = "NOT_PROVEN"

        result = TaskResult(
            request.task_id,
            capability,
            "PASS",
            execution,
            verification,
            final_state,
        )
        self.ledger.append(task_id=request.task_id, event="verification", result=verification)
        self._idempotency[request.idempotency_key] = result
        return result

    @staticmethod
    def _default_executor(resource: InMemoryResource, intended_value: str) -> bool:
        resource.value = intended_value
        resource.revision += 1
        return True

    @staticmethod
    def _default_verifier(resource: InMemoryResource, intended_value: str) -> bool:
        return resource.value == intended_value
