"""Задача (аналог Reader в лабораторной: «получатель» агента) и события аудита."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from .exceptions import InvalidTaskStateError


class TaskStatus(str, Enum):
    PENDING = "pending"      # создана, агент не назначен
    ASSIGNED = "assigned"    # назначена агенту
    DONE = "done"            # выполнена


class Task:
    def __init__(self, task_id: str, description: str, capability: str = "") -> None:
        if not task_id or not description:
            raise ValueError("task_id и description обязательны")
        self._task_id = task_id
        self._description = description
        self._capability = capability.strip().lower()
        self._status = TaskStatus.PENDING
        self._agent_id: Optional[str] = None
        self._result: Optional[str] = None

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def description(self) -> str:
        return self._description

    @property
    def capability(self) -> str:
        return self._capability

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def agent_id(self) -> Optional[str]:
        return self._agent_id

    @property
    def result(self) -> Optional[str]:
        return self._result

    # Переходы состояний: единственное место, где меняется статус.
    def assign(self, agent_id: str) -> None:
        if self._status is not TaskStatus.PENDING:
            raise InvalidTaskStateError(f"Задача {self._task_id} уже имеет статус {self._status.value}")
        self._status, self._agent_id = TaskStatus.ASSIGNED, agent_id

    def unassign(self) -> None:
        if self._status is not TaskStatus.ASSIGNED:
            raise InvalidTaskStateError(f"Задача {self._task_id} не назначена (статус {self._status.value})")
        self._status, self._agent_id = TaskStatus.PENDING, None

    def complete(self, result: str) -> None:
        if self._status is not TaskStatus.ASSIGNED:
            raise InvalidTaskStateError(f"Задача {self._task_id} не назначена (статус {self._status.value})")
        self._status, self._result = TaskStatus.DONE, result

    def display(self) -> str:
        return (f"[{self._task_id}] {self._description} | навык: {self._capability or 'любой'} | "
                f"статус: {self._status.value} | агент: {self._agent_id or '-'}")

    def to_dict(self) -> Dict[str, Any]:
        return {"task_id": self._task_id, "description": self._description,
                "capability": self._capability, "status": self._status.value,
                "agent_id": self._agent_id, "result": self._result}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Task":
        t = cls(d["task_id"], d["description"], d.get("capability", ""))
        t._status = TaskStatus(d.get("status", "pending"))
        t._agent_id = d.get("agent_id")
        t._result = d.get("result")
        return t


@dataclass(frozen=True)
class AuditEvent:
    """Запись журнала центрального управления: кто, что и когда сделал."""
    event: str
    details: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __str__(self) -> str:
        return f"{self.timestamp} {self.event}: {self.details}"
