# Каркас кода диссертации: централизованное управление ИИ-агентами

Python 3.9+, без внешних зависимостей. Реальные модели (локальные и по API) пока не подключены:
точка подключения — `Agent.attach_runner(callable)`.

```
code/
  main.py                    # консольное меню
  demo_session.py            # скриптованный прогон меню (для отчёта)
  agent_control/
    agents/                  # Agent (абстрактный) <- LocalModelAgent, ApiModelAgent, DummyAgent
    task.py                  # Task, TaskStatus, AuditEvent
    policies.py              # DispatchPolicy <- FirstFitPolicy, LeastLoadedPolicy (метод распределения)
    orchestrator.py          # Orchestrator: центр управления (регистрация, назначение, выполнение, аудит, JSON)
    exceptions.py            # иерархия AgentControlError
    cli.py                   # Menu
  tests/                   # pytest: тесты агентов, задач, политик, оркестратора, хранения и меню
```

Запуск: `python main.py`; тесты: `pip install -r requirements-dev.txt`, затем `python -m pytest` (покрытие: `python -m pytest --cov=agent_control --cov-branch`).
