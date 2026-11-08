"""Фабрика агентов по строковому типу."""
from __future__ import annotations

from typing import Iterable, Tuple

from .base import Agent, agent_types


class AgentFactory:
    @staticmethod
    def _type(kind: str) -> type:
        try:
            return agent_types()[kind.strip().lower()]
        except KeyError:
            raise ValueError(f"неизвестный тип {kind!r}") from None

    @staticmethod
    def option_prompts(kind: str) -> Tuple[Tuple[str, str, str], ...]:
        return AgentFactory._type(kind).OPTIONS

    @staticmethod
    def create(kind: str, agent_id: str, name: str, capabilities: Iterable[str] = (),
               capacity: int = 1, **options) -> Agent:
        return AgentFactory._type(kind)(agent_id, name, capabilities, capacity, **options)
