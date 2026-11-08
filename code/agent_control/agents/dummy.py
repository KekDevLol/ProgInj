"""Агент-заглушка для отладки и тестов."""
from __future__ import annotations

from typing import Any, Dict

from .base import Agent, register_agent


@register_agent
class DummyAgent(Agent):
    TYPE = "dummy"

    def get_type(self) -> str:
        return "Заглушка"

    def display(self) -> str:
        return self._summary()

    def execute(self, prompt: str) -> str:
        if self._runner is not None:
            return self._runner(prompt)
        return f"[dummy:{self._agent_id}] выполнено: {prompt}"

    def _extra_dict(self) -> Dict[str, Any]:
        return {}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DummyAgent":
        return cls(d["agent_id"], d["name"], d.get("capabilities", ()), d.get("capacity", 1))
