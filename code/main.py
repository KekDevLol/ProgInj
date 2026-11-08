"""Точка входа: python main.py"""
import sys

from agent_control.cli import Menu
from agent_control.orchestrator import Orchestrator

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    Menu(Orchestrator.instance()).loop()
