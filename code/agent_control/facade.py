"""Фасад: типовые сценарии одним вызовом."""
from __future__ import annotations

from .orchestrator import Orchestrator
from .task import Task


class ControlFacade:
    def __init__(self, orchestrator: Orchestrator) -> None:
        self._orc = orchestrator

    def run_task(self, description: str, capability: str = "") -> Task:
        task = self._orc.create_task(description, capability)
        self._orc.dispatch(task.task_id)
        return self._orc.execute_task(task.task_id)
