from pathlib import Path

from agent_control import Orchestrator
from agent_control.cli import Menu


def run_menu(answers, orc=None, tmp_path=None):
    it = iter(answers)
    out = []

    def fake_input(prompt):
        out.append(prompt)
        try:
            return next(it)
        except StopIteration:
            raise EOFError from None

    Menu(orc or Orchestrator(), fake_input, out.append, (tmp_path or Path(".")) / "s.json").loop()
    return "\n".join(out)


ADD_DUMMY = ["1", "dummy", "d1", "Аналитик", "text,analysis", "2"]
ADD_TASK = ["2", "Обзор литературы", "analysis"]


def test_exit_and_unknown_item():
    out = run_menu(["99", "0"])
    assert "Неизвестный пункт" in out and "До свидания" in out


def test_add_agent_each_type_and_errors():
    out = run_menu(["1", "local", "l1", "L", "code", "1", "D:/m", "cuda",
                    "1", "api", "a1", "A", "text", "1", "https://x", "KEY"] + ADD_DUMMY
                   + ["1", "robot", "r", "R", "", "1", "1", "dummy", "d", "D", "", "abc", "0"])
    assert out.count("Агент зарегистрирован") == 3
    assert out.count("Некорректные данные") == 2


def test_add_task_and_manual_assign():
    out = run_menu(ADD_DUMMY + ADD_TASK + ["3", "T1", "d1", "3", "T9", "d1", "0"])
    assert "Создана задача T1" in out and "Задача назначена." in out
    assert "Задача 'T9' не найдена" in out


def test_dispatch_execute_and_unassign():
    out = run_menu(ADD_DUMMY + ADD_TASK + ["4", "T1", "5", "T1", "6", "T1", "0"])
    assert "назначена агенту d1" in out and "Результат: [dummy:d1]" in out
    assert "не назначена" in out


def test_search_lists_and_report():
    out = run_menu(["8", "9", "10"] + ADD_DUMMY + ADD_TASK
                   + ["7", "аналит", "", "", "7", "zzz", "", "", "9", "11", "0"])
    assert "Агентов нет" in out and "Журнал пуст" in out
    assert "[d1] Аналитик" in out and "Ничего не найдено" in out
    assert "[T1] Обзор литературы" in out and "Политика: least-loaded" in out


def test_change_policy():
    out = run_menu(["12", "first-fit", "12", "random", "0"])
    assert "Политика: first-fit" in out and "неизвестная политика" in out


def test_save_and_load(tmp_path):
    run_menu(ADD_DUMMY + ["13", "0"], Orchestrator(), tmp_path)
    out = run_menu(["14", "8", "0"], None, tmp_path)
    assert "Загружено" in out and "[d1] Аналитик" in out


def test_input_closed_does_not_crash():
    assert "Ввод завершён" in run_menu([])
