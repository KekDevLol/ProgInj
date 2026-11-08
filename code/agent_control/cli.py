"""Консольное меню."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from .agents import Agent, ApiModelAgent, DummyAgent, LocalModelAgent
from .exceptions import AgentControlError
from .orchestrator import Orchestrator
from .policies import FirstFitPolicy, LeastLoadedPolicy

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data" / "state.json"

MENU = """
=== Централизованное управление ИИ-агентами ===
1. Зарегистрировать агента
2. Создать задачу
3. Назначить задачу агенту (вручную)
4. Назначить задачу автоматически (политика)
5. Выполнить задачу
6. Вернуть задачу в очередь
7. Поиск агента
8. Вывести всех агентов
9. Вывести все задачи
10. Журнал аудита
11. Отчёт
12. Сменить политику распределения
13. Сохранить в файл
14. Загрузить из файла
0. Выход
"""


class Menu:
    def __init__(self, orchestrator: Orchestrator, input_fn: Callable[[str], str] = input,
                 output_fn: Callable[[str], None] = print, data_path: Path = DEFAULT_DATA) -> None:
        self._orc = orchestrator
        self._in = input_fn
        self._out = output_fn
        self._path = data_path
        self._actions = {
            "1": self._add_agent, "2": self._add_task, "3": self._assign, "4": self._dispatch,
            "5": self._execute, "6": self._unassign, "7": self._search, "8": self._list_agents,
            "9": self._list_tasks, "10": self._audit, "11": self._report, "12": self._policy,
            "13": self._save, "14": self._load,
        }

    def loop(self) -> None:
        while True:
            self._out(MENU)
            choice = self._in("Выбор: ").strip()
            if choice == "0":
                self._out("До свидания.")
                return
            action = self._actions.get(choice)
            if action is None:
                self._out("Неизвестный пункт меню.")
                continue
            try:
                action()
            except AgentControlError as exc:
                self._out(f"Ошибка: {exc}")
            except ValueError as exc:
                self._out(f"Некорректные данные: {exc}")

    def _ask(self, label: str) -> str:
        return self._in(label).strip()

    def _add_agent(self) -> None:
        kind = self._ask("Тип (local/api/dummy): ").lower()
        agent_id, name = self._ask("ID агента: "), self._ask("Название: ")
        caps = [c for c in self._ask("Навыки через запятую: ").split(",")]
        capacity = int(self._ask("Лимит одновременных задач (1): ") or 1)
        agent: Agent
        if kind == "local":
            agent = LocalModelAgent(agent_id, name, caps, capacity,
                                    self._ask("Путь к весам: "), self._ask("Устройство (cpu/cuda): ") or "cpu")
        elif kind == "api":
            agent = ApiModelAgent(agent_id, name, caps, capacity, self._ask("Base URL: "),
                                  self._ask("Имя переменной окружения с ключом: "))
        elif kind == "dummy":
            agent = DummyAgent(agent_id, name, caps, capacity)
        else:
            raise ValueError(f"неизвестный тип {kind!r}")
        self._orc.register_agent(agent)
        self._out("Агент зарегистрирован.")

    def _add_task(self) -> None:
        task = self._orc.create_task(self._ask("Описание задачи: "), self._ask("Требуемый навык (пусто = любой): "))
        self._out(f"Создана задача {task.task_id}.")

    def _assign(self) -> None:
        self._orc.assign(self._ask("ID задачи: "), self._ask("ID агента: "))
        self._out("Задача назначена.")

    def _dispatch(self) -> None:
        agent = self._orc.dispatch(self._ask("ID задачи: "))
        self._out(f"Задача назначена агенту {agent.agent_id} (политика {self._orc.policy.name}).")

    def _execute(self) -> None:
        task = self._orc.execute_task(self._ask("ID задачи: "))
        self._out(f"Результат: {task.result}")

    def _unassign(self) -> None:
        self._orc.unassign(self._ask("ID задачи: "))
        self._out("Задача возвращена в очередь.")

    def _search(self) -> None:
        found = self._orc.find_agents(self._in("Часть названия/ID: "), self._ask("Навык (пусто = любой): "),
                                      self._ask("Тип (пусто = любой): "))
        self._out("\n".join(a.display() for a in found) if found else "Ничего не найдено.")

    def _list_agents(self) -> None:
        agents = self._orc.agents
        self._out("\n".join(a.display() for a in agents) if agents else "Агентов нет.")

    def _list_tasks(self) -> None:
        tasks = self._orc.tasks
        self._out("\n".join(t.display() for t in tasks) if tasks else "Задач нет.")

    def _audit(self) -> None:
        events = self._orc.audit_log
        self._out("\n".join(str(e) for e in events) if events else "Журнал пуст.")

    def _report(self) -> None:
        self._out(self._orc.report())

    def _policy(self) -> None:
        name = self._ask("Политика (first-fit / least-loaded): ")
        policies = {"first-fit": FirstFitPolicy, "least-loaded": LeastLoadedPolicy}
        if name not in policies:
            raise ValueError(f"неизвестная политика {name!r}")
        self._orc.set_policy(policies[name]())
        self._out(f"Политика: {name}")

    def _save(self) -> None:
        self._orc.save(self._path)
        self._out(f"Сохранено: {self._path}")

    def _load(self) -> None:
        self._orc = Orchestrator.load(self._path, self._orc.policy)
        self._out(f"Загружено: {self._path}")
