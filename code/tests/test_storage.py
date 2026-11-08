import json

import pytest

from agent_control import LocalModelAgent, Orchestrator, TaskStatus
from agent_control.exceptions import StorageError


def test_roundtrip(orc, tmp_path):
    t = orc.create_task("x", "text")
    orc.assign(t.task_id, "d1")
    path = tmp_path / "state.json"
    orc.save(path)
    loaded = Orchestrator.load(path)
    assert [a.agent_id for a in loaded.agents] == [a.agent_id for a in orc.agents]
    assert loaded.get_agent("d1").load == 1
    assert loaded.get_task("T1").status is TaskStatus.ASSIGNED
    assert loaded.create_task("y").task_id == "T2"
    assert isinstance(loaded.get_agent("l1"), LocalModelAgent)


def test_save_creates_missing_folder(orc, tmp_path):
    path = tmp_path / "a" / "b" / "state.json"
    orc.save(path)
    assert path.exists()


def test_load_missing_file(tmp_path):
    with pytest.raises(StorageError):
        Orchestrator.load(tmp_path / "none.json")


def test_load_broken_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(StorageError):
        Orchestrator.load(path)


def test_load_unknown_agent_type(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"agents": [{"type": "alien", "agent_id": "x", "name": "x"}], "tasks": []}),
                    encoding="utf-8")
    with pytest.raises(StorageError):
        Orchestrator.load(path)


def test_load_task_with_unknown_agent(tmp_path):
    state = {"agents": [], "tasks": [{"task_id": "T1", "description": "x", "status": "assigned",
                                      "agent_id": "ghost"}]}
    path = tmp_path / "s.json"
    path.write_text(json.dumps(state), encoding="utf-8")
    with pytest.raises(StorageError):
        Orchestrator.load(path)
