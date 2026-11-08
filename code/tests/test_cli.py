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

    menu = Menu(orc or Orchestrator(), fake_input, out.append, (tmp_path or Path(".")) / "s.json")
    menu.loop()
    return "\n".join(out)


ADD_DUMMY = ["1", "dummy", "d1", "Аналитик", "text,analysis", "2"]
ADD_TASK = ["2", "Обзор литературы", "analysis"]


def test_menu_exit():
    assert "До свидания" in run_menu(["0"])


def test_unknown_menu_item():
    assert "Неизвестный пункт" in run_menu(["99", "0"])


def test_add_agent_each_type():
    out = run_menu(["1", "local", "l1", "L", "code", "1", "D:/m", "cuda",
                    "1", "api", "a1", "A", "text", "1", "https://x", "KEY",
                    "1", "dummy", "d1", "D", "", "", "8", "0"])
    assert out.count("Агент зарегистрирован") == 3
    assert "Локальная модель" in out and "API-агент" in out and "Заглушка" in out


def test_add_agent_unknown_type():
    assert "Некорректные данные" in run_menu(["1", "robot", "r", "R", "", "1", "0"])


def test_add_agent_bad_capacity():
    assert "Некорректные данные" in run_menu(["1", "dummy", "d", "D", "", "abc", "0"])


def test_add_agent_duplicate():
    out = run_menu(ADD_DUMMY + ADD_DUMMY + ["0"])
    assert "уже зарегистрирован" in out


def test_add_task():
    assert "Создана задача T1" in run_menu(ADD_DUMMY + ADD_TASK + ["0"])


def test_manual_assign():
    assert "Задача назначена." in run_menu(ADD_DUMMY + ADD_TASK + ["3", "T1", "d1", "0"])


def test_assign_unknown_task_and_agent():
    out = run_menu(ADD_DUMMY + ADD_TASK + ["3", "T9", "d1", "3", "T1", "zzz", "0"])
    assert "Задача 'T9' не найдена" in out and "Агент 'zzz' не найден" in out


def test_dispatch_and_execute():
    out = run_menu(ADD_DUMMY + ADD_TASK + ["4", "T1", "5", "T1", "0"])
    assert "назначена агенту d1" in out and "Результат: [dummy:d1]" in out


def test_dispatch_without_agent():
    out = run_menu(ADD_DUMMY + ["2", "Картинка", "vision", "4", "T1", "0"])
    assert "нет свободного агента" in out


def test_unassign():
    out = run_menu(ADD_DUMMY + ADD_TASK + ["3", "T1", "d1", "6", "T1", "0"])
    assert "возвращена в очередь" in out


def test_unassign_pending_task():
    assert "не назначена" in run_menu(ADD_DUMMY + ADD_TASK + ["6", "T1", "0"])


def test_search_menu():
    out = run_menu(ADD_DUMMY + ["7", "аналит", "", "", "7", "zzz", "", "", "0"])
    assert "[d1] Аналитик" in out and "Ничего не найдено" in out


def test_lists_on_empty_state():
    out = run_menu(["8", "9", "10", "0"])
    assert "Агентов нет" in out and "Задач нет" in out and "Журнал пуст" in out


def test_lists_after_work():
    out = run_menu(ADD_DUMMY + ADD_TASK + ["8", "9", "10", "0"])
    assert "[d1] Аналитик" in out and "[T1] Обзор литературы" in out and "register: d1" in out


def test_report():
    assert "Политика: least-loaded" in run_menu(ADD_DUMMY + ["11", "0"])


def test_change_policy():
    out = run_menu(["12", "first-fit", "12", "random", "0"])
    assert "Политика: first-fit" in out and "неизвестная политика" in out


def test_save_and_load(tmp_path):
    orc = Orchestrator()
    run_menu(ADD_DUMMY + ADD_TASK + ["13", "0"], orc, tmp_path)
    out = run_menu(["14", "8", "0"], None, tmp_path)
    assert "Загружено" in out and "[d1] Аналитик" in out


def test_load_missing_file(tmp_path):
    assert "Не удалось загрузить" in run_menu(["14", "0"], None, tmp_path)


def test_input_closed_does_not_crash():
    out = run_menu([])
    assert "Ввод завершён" in out
