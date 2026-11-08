"""Прогон меню скриптованным вводом."""
import sys
import tempfile
from pathlib import Path

from agent_control.cli import Menu
from agent_control.orchestrator import Orchestrator

INPUTS = [
    "1", "dummy", "d1", "Агент-аналитик", "text,analysis", "2",
    "1", "dummy", "d2", "Агент-кодер", "code", "1",
    "1", "local", "l1", "Llama локально", "text,code", "1", "D:/models/llama3", "cuda",
    "1", "api", "a1", "Облачный агент", "text", "3", "https://api.example.com/v1", "LLM_API_KEY",
    "2", "Составить обзор литературы", "analysis",
    "2", "Написать функцию сортировки", "code",
    "2", "Распознать изображение", "vision",
    "4", "T1",
    "4", "T3",
    "3", "T2", "d1",
    "3", "T2", "d2",
    "3", "T2", "d2",
    "3", "T9", "d1",
    "3", "T1", "zzz",
    "5", "T1",
    "5", "T2",
    "6", "T2",
    "2", "Перевести текст", "text",
    "4", "T4",
    "5", "T4",
    "7", "llam", "", "",
    "7", "", "code", "",
    "12", "first-fit",
    "11", "10", "13", "14",
    "6", "T1",
    "0",
]

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    it = iter(INPUTS)

    def fake_input(prompt: str) -> str:
        value = next(it)
        print(f"{prompt}{value}")
        return value

    with tempfile.TemporaryDirectory() as tmp:
        Menu(Orchestrator(), fake_input, print, Path(tmp) / "state.json").loop()
