"""Агент, работающий через HTTP API провайдера. Секрет не хранится: только имя переменной
окружения, из которой ключ будет прочитан при подключении клиента."""
from __future__ import annotations

from typing import Any, Dict, Iterable

from ..exceptions import AgentNotConnectedError
from .base import Agent, register_agent


@register_agent
class ApiModelAgent(Agent):
    TYPE = "api"

    def __init__(self, agent_id: str, name: str, capabilities: Iterable[str] = (), capacity: int = 1,
                 base_url: str = "", api_key_env: str = "", timeout_s: float = 60.0) -> None:
        super().__init__(agent_id, name, capabilities, capacity)
        self._base_url = base_url
        self._api_key_env = api_key_env
        self._timeout_s = timeout_s

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def api_key_env(self) -> str:
        return self._api_key_env

    @property
    def timeout_s(self) -> float:
        return self._timeout_s

    def get_type(self) -> str:
        return "API-агент"

    def display(self) -> str:
        state = "подключён" if self.is_connected else "не подключён"
        return (f"{self._summary()} | url: {self._base_url or '-'} | "
                f"ключ из env: {self._api_key_env or '-'} | {state}")

    def execute(self, prompt: str) -> str:
        if self._runner is None:
            # TODO(диссертация): HTTP-клиент провайдера через attach_runner().
            raise AgentNotConnectedError(f"API-агент {self._agent_id} не подключён")
        return self._runner(prompt)

    def _extra_dict(self) -> Dict[str, Any]:
        return {"base_url": self._base_url, "api_key_env": self._api_key_env,
                "timeout_s": self._timeout_s}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ApiModelAgent":
        return cls(d["agent_id"], d["name"], d.get("capabilities", ()), d.get("capacity", 1),
                   d.get("base_url", ""), d.get("api_key_env", ""), d.get("timeout_s", 60.0))
