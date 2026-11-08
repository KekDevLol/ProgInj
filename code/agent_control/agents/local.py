"""Агент на локальной модели (веса на машине пользователя). Инференс пока не подключён."""
from __future__ import annotations

from typing import Any, Dict, Iterable

from ..exceptions import AgentNotConnectedError
from .base import Agent, register_agent


@register_agent
class LocalModelAgent(Agent):
    TYPE = "local"

    def __init__(self, agent_id: str, name: str, capabilities: Iterable[str] = (), capacity: int = 1,
                 model_path: str = "", device: str = "cpu") -> None:
        super().__init__(agent_id, name, capabilities, capacity)
        self._model_path = model_path
        self._device = device

    @property
    def model_path(self) -> str:
        return self._model_path

    @property
    def device(self) -> str:
        return self._device

    def get_type(self) -> str:
        return "Локальная модель"

    def display(self) -> str:
        state = "подключён" if self.is_connected else "не подключён"
        return f"{self._summary()} | путь: {self._model_path or '-'} | {self._device} | {state}"

    def execute(self, prompt: str) -> str:
        if self._runner is None:
            # TODO(диссертация): transformers / llama.cpp / Ollama через attach_runner().
            raise AgentNotConnectedError(f"Локальный агент {self._agent_id} не подключён")
        return self._runner(prompt)

    def _extra_dict(self) -> Dict[str, Any]:
        return {"model_path": self._model_path, "device": self._device}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LocalModelAgent":
        return cls(d["agent_id"], d["name"], d.get("capabilities", ()), d.get("capacity", 1),
                   d.get("model_path", ""), d.get("device", "cpu"))
