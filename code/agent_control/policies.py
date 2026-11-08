"""Политики выбора агента для задачи."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from .agents import Agent
from .task import Task


class DispatchPolicy(ABC):
    name = "abstract"

    @abstractmethod
    def select(self, candidates: Sequence[Agent], task: Task) -> Agent:
        """Выбрать одного агента из непустого списка кандидатов."""


class FirstFitPolicy(DispatchPolicy):
    name = "first-fit"

    def select(self, candidates: Sequence[Agent], task: Task) -> Agent:
        return candidates[0]


class LeastLoadedPolicy(DispatchPolicy):
    name = "least-loaded"

    def select(self, candidates: Sequence[Agent], task: Task) -> Agent:
        return min(candidates, key=lambda a: a.load / a.capacity)
