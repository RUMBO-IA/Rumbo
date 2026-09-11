from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class TaskRequest:
    task_id: str
    intended_value: str
    authority_token: Optional[str]
    idempotency_key: str
    revision: int

@dataclass(frozen=True)
class TaskResult:
    task_id: str
    capability: str
    authority: str
    execution: str
    verification: str
    final_state: str
    detail: str = ""
