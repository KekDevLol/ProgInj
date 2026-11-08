"""Базовый класс агента."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, FrozenSet, Iterable, List, Optional, Type

Runner = Callable[[str], str]

_AGENT_TYPES: Dict[str, Type["Agent"]] = {}


def register_agent(cls: Type["Agent"]) -> Type["Agent"]:
    _AGENT_TYPES[cls.TYPE] = cls
    return cls


def agent_types() -> Dict[str, Type["Agent"]]:
    return dict(_AGENT_TYPES)


def agent_from_dict(data: Dict[str, Any]) -> "Agent":
    try:
        cls = _AGENT_TYPES[data["type"]]
    except KeyError as exc:
        raise ValueError(f"Неизвестный тип агента: {data.get('type')!r}") from exc
    return cls.from_dict(data)


class Agent(ABC):
    TYPE = "abstract"
    OPTIONS: tuple = ()

    def __init__(self, agent_id: str, name: str, capabilities: Iterable[str] = (),
                 capacity: int = 1) -> None:
        if not agent_id.strip() or not name.strip():
            raise ValueError("agent_id и name обязательны")
        if capacity < 1:
            raise ValueError("capacity должна быть >= 1")
        self._agent_id = agent_id
        self._name = name
        self._capabilities: FrozenSet[str] = frozenset(c.strip().lower() for c in capabilities if c.strip())
        self._capacity = capacity
        self._active: List[str] = []
        self._runner: Optional[Runner] = None

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> FrozenSet[str]:
        return self._capabilities

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def active_tasks(self) -> List[str]:
        return list(self._active)

    @property
    def load(self) -> int:
        return len(self._active)

    @property
    def has_capacity(self) -> bool:
        return self.load < self._capacity

    @property
    def is_connected(self) -> bool:
        return self._runner is not None

    def can_handle(self, capability: str) -> bool:
        return not capability or capability.strip().lower() in self._capabilities

    def attach_runner(self, runner: Runner) -> None:
        self._runner = runner

    def assign_task(self, task_id: str) -> None:
        self._active.append(task_id)

    def finish_task(self, task_id: str) -> None:
        self._active.remove(task_id)

    @abstractmethod
    def get_type(self) -> str:
        """Человекочитаемый тип агента."""

    @abstractmethod
    def display(self) -> str:
        """Описание для консоли."""

    @abstractmethod
    def execute(self, prompt: str) -> str:
        """Выполнить задачу и вернуть результат."""

    @abstractmethod
    def _extra_dict(self) -> Dict[str, Any]:
        """Поля наследника для сохранения."""

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Восстановление из словаря."""

    def _summary(self) -> str:
        return (f"[{self._agent_id}] {self._name} | {self.get_type()} | "
                f"навыки: {', '.join(sorted(self._capabilities)) or '-'} | "
                f"загрузка: {self.load}/{self._capacity}")

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.TYPE, "agent_id": self._agent_id, "name": self._name,
                "capabilities": sorted(self._capabilities), "capacity": self._capacity,
                **self._extra_dict()}

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self._agent_id}>"
