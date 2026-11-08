"""Центр управления: все действия с агентами и задачами идут через него."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

from .agents import Agent, agent_from_dict
from .exceptions import (AgentBusyError, AgentNotFoundError, CapabilityMismatchError,
                         DuplicateIdError, NoSuitableAgentError, StorageError, TaskNotFoundError)
from .policies import DispatchPolicy, LeastLoadedPolicy
from .task import AuditEvent, Task, TaskStatus


class Orchestrator:
    def __init__(self, policy: Optional[DispatchPolicy] = None) -> None:
        self._agents: Dict[str, Agent] = {}
        self._tasks: Dict[str, Task] = {}
        self._audit: List[AuditEvent] = []
        self._policy: DispatchPolicy = policy or LeastLoadedPolicy()
        self._task_counter = 0

    @property
    def policy(self) -> DispatchPolicy:
        return self._policy

    def set_policy(self, policy: DispatchPolicy) -> None:
        self._policy = policy
        self._log("policy", f"установлена политика {policy.name}")

    def get_agent(self, agent_id: str) -> Agent:
        try:
            return self._agents[agent_id]
        except KeyError:
            raise AgentNotFoundError(f"Агент {agent_id!r} не найден") from None

    def get_task(self, task_id: str) -> Task:
        try:
            return self._tasks[task_id]
        except KeyError:
            raise TaskNotFoundError(f"Задача {task_id!r} не найдена") from None

    @property
    def agents(self) -> List[Agent]:
        return list(self._agents.values())

    @property
    def tasks(self) -> List[Task]:
        return list(self._tasks.values())

    @property
    def audit_log(self) -> List[AuditEvent]:
        return list(self._audit)

    def _log(self, event: str, details: str) -> None:
        self._audit.append(AuditEvent(event, details))

    def register_agent(self, agent: Agent) -> None:
        if agent.agent_id in self._agents:
            raise DuplicateIdError(f"Агент {agent.agent_id} уже зарегистрирован")
        self._agents[agent.agent_id] = agent
        self._log("register", f"{agent.agent_id} ({agent.get_type()})")

    def create_task(self, description: str, capability: str = "") -> Task:
        self._task_counter += 1
        task = Task(f"T{self._task_counter}", description, capability)
        self._tasks[task.task_id] = task
        self._log("create", f"{task.task_id}: {description}")
        return task

    def find_agents(self, query: str = "", capability: str = "", type_name: str = "") -> List[Agent]:
        q = query.strip().lower()
        return [a for a in self._agents.values()
                if (not q or q in a.name.lower() or q in a.agent_id.lower())
                and a.can_handle(capability)
                and (not type_name or a.TYPE == type_name)]

    def assign(self, task_id: str, agent_id: str) -> None:
        task = self.get_task(task_id)
        agent = self.get_agent(agent_id)
        if task.status is not TaskStatus.PENDING:
            task.assign(agent_id)
        if not agent.can_handle(task.capability):
            raise CapabilityMismatchError(
                f"Агент {agent_id} не обладает навыком {task.capability!r}")
        if not agent.has_capacity:
            raise AgentBusyError(f"У агента {agent_id} нет свободных слотов ({agent.load}/{agent.capacity})")
        task.assign(agent_id)
        agent.assign_task(task_id)
        self._log("assign", f"{task_id} -> {agent_id}")

    def dispatch(self, task_id: str) -> Agent:
        task = self.get_task(task_id)
        candidates = [a for a in self._agents.values()
                      if a.can_handle(task.capability) and a.has_capacity]
        if not candidates:
            raise NoSuitableAgentError(f"Для задачи {task_id} нет свободного агента с навыком "
                                       f"{task.capability or 'любой'!r}")
        agent = self._policy.select(candidates, task)
        self.assign(task_id, agent.agent_id)
        return agent

    def unassign(self, task_id: str) -> None:
        task = self.get_task(task_id)
        agent_id = task.agent_id
        task.unassign()
        if agent_id:
            self.get_agent(agent_id).finish_task(task_id)
        self._log("unassign", f"{task_id} <- {agent_id}")

    def execute_task(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        if task.status is not TaskStatus.ASSIGNED:
            task.complete("")
        agent = self.get_agent(task.agent_id)   # type: ignore[arg-type]
        try:
            result = agent.execute(task.description)
        except Exception as exc:
            self._log("execute_failed", f"{task_id} @ {agent.agent_id}: {exc}")
            raise
        task.complete(result)
        agent.finish_task(task_id)
        self._log("execute", f"{task_id} @ {agent.agent_id} -> готово")
        return task

    def report(self) -> str:
        by_status = {s: sum(1 for t in self._tasks.values() if t.status is s) for s in TaskStatus}
        lines = [f"Политика: {self._policy.name}",
                 f"Агентов: {len(self._agents)}, задач: {len(self._tasks)} "
                 f"(ожидают: {by_status[TaskStatus.PENDING]}, в работе: {by_status[TaskStatus.ASSIGNED]}, "
                 f"готово: {by_status[TaskStatus.DONE]})", "", "Агенты:"]
        lines += [f"  {a.display()}" for a in self._agents.values()]
        lines += ["", "Задачи:"] + [f"  {t.display()}" for t in self._tasks.values()]
        return "\n".join(lines)

    def save(self, path: Union[str, Path]) -> None:
        data = {"policy": self._policy.name, "task_counter": self._task_counter,
                "agents": [a.to_dict() for a in self._agents.values()],
                "tasks": [t.to_dict() for t in self._tasks.values()],
                "audit": [e.to_dict() for e in self._audit]}
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Не удалось сохранить: {exc}") from exc

    @classmethod
    def load(cls, path: Union[str, Path], policy: Optional[DispatchPolicy] = None) -> "Orchestrator":
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            orch = cls(policy)
            for a in data["agents"]:
                agent = agent_from_dict(a)
                orch._agents[agent.agent_id] = agent
            for t in data["tasks"]:
                task = Task.from_dict(t)
                orch._tasks[task.task_id] = task
                if task.status is TaskStatus.ASSIGNED and task.agent_id in orch._agents:
                    orch._agents[task.agent_id].assign_task(task.task_id)
            orch._audit = [AuditEvent(**e) for e in data.get("audit", [])]
            orch._task_counter = int(data.get("task_counter", len(orch._tasks)))
            return orch
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise StorageError(f"Не удалось загрузить {path}: {exc}") from exc
