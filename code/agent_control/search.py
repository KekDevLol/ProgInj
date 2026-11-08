"""Стратегии поиска агентов."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .agents import Agent


class SearchStrategy(ABC):
    @abstractmethod
    def matches(self, agent: Agent, query: str) -> bool:
        """Подходит ли агент под запрос. Пустой запрос подходит всем."""


class SearchByName(SearchStrategy):
    def matches(self, agent: Agent, query: str) -> bool:
        q = query.strip().lower()
        return not q or q in agent.name.lower() or q in agent.agent_id.lower()


class SearchByCapability(SearchStrategy):
    def matches(self, agent: Agent, query: str) -> bool:
        return agent.can_handle(query)


class SearchByType(SearchStrategy):
    def matches(self, agent: Agent, query: str) -> bool:
        return not query or agent.TYPE == query
