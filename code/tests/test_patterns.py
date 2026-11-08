import threading

import pytest

from agent_control import (AgentFactory, ApiModelAgent, ControlFacade, DummyAgent, LocalModelAgent,
                           Orchestrator, TaskStatus)
from agent_control.search import SearchByCapability, SearchByName, SearchByType


@pytest.fixture(autouse=True)
def clean_singleton():
    Orchestrator.reset_instance()
    yield
    Orchestrator.reset_instance()


def test_singleton_returns_same_object():
    assert Orchestrator.instance() is Orchestrator.instance()


def test_singleton_same_object_in_threads():
    found = []
    threads = [threading.Thread(target=lambda: found.append(Orchestrator.instance())) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len({id(o) for o in found}) == 1


def test_singleton_reset_creates_new_object():
    first = Orchestrator.instance()
    Orchestrator.reset_instance()
    assert Orchestrator.instance() is not first


@pytest.mark.parametrize("kind, cls", [("local", LocalModelAgent), ("API", ApiModelAgent), ("dummy", DummyAgent)])
def test_factory_creates_each_type(kind, cls):
    assert isinstance(AgentFactory.create(kind, "a", "A", ["text"], 2), cls)


def test_factory_passes_options():
    agent = AgentFactory.create("local", "l", "L", model_path="D:/m", device="cuda")
    assert (agent.model_path, agent.device) == ("D:/m", "cuda")


def test_factory_unknown_type():
    with pytest.raises(ValueError):
        AgentFactory.create("robot", "r", "R")


def test_factory_option_prompts():
    assert [k for k, _, _ in AgentFactory.option_prompts("api")] == ["base_url", "api_key_env"]
    assert AgentFactory.option_prompts("dummy") == ()


def test_search_by_name(orc):
    assert [a.agent_id for a in orc.search("llama", SearchByName())] == ["l1"]


def test_search_by_capability(orc):
    assert {a.agent_id for a in orc.search("code", SearchByCapability())} == {"d1", "l1"}


def test_search_by_type(orc):
    assert [a.agent_id for a in orc.search("api", SearchByType())] == ["a1"]


def test_search_empty_query_matches_all(orc):
    assert len(orc.search("", SearchByName())) == 4


def test_facade_runs_task_in_one_call(orc):
    task = ControlFacade(orc).run_task("перевести", "text")
    assert task.status is TaskStatus.DONE and task.agent_id is not None
