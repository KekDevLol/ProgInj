"""Политики распределения задач (паттерн «Стратегия»).

Метод централизованного управления выделен в сменяемый объект: оркестратор отдаёт политике
список подходящих агентов, а выбор делает она. Для диссертации здесь будут появляться
новые политики (по стоимости, по качеству, по очереди и т.д.) без изменения оркестратора."""
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
    """Первый подходящий (порядок регистрации)."""
    name = "first-fit"

    def select(self, candidates: Sequence[Agent], task: Task) -> Agent:
        return candidates[0]


class LeastLoadedPolicy(DispatchPolicy):
    """Агент с наименьшей относительной загрузкой (балансировка нагрузки)."""
    name = "least-loaded"

    def select(self, candidates: Sequence[Agent], task: Task) -> Agent:
        return min(candidates, key=lambda a: a.load / a.capacity)
