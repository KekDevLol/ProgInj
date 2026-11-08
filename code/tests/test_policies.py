import pytest

from agent_control import DispatchPolicy, DummyAgent, FirstFitPolicy, LeastLoadedPolicy, Task


@pytest.fixture
def agents():
    busy = DummyAgent("busy", "Busy", capacity=2)
    busy.assign_task("T0")
    return [busy, DummyAgent("idle", "Idle", capacity=2)]


def test_policy_is_abstract():
    with pytest.raises(TypeError):
        DispatchPolicy()


def test_first_fit_takes_first(agents):
    assert FirstFitPolicy().select(agents, Task("T1", "x")).agent_id == "busy"


def test_least_loaded_takes_idle(agents):
    assert LeastLoadedPolicy().select(agents, Task("T1", "x")).agent_id == "idle"


def test_least_loaded_uses_relative_load():
    small = DummyAgent("small", "S", capacity=1)
    big = DummyAgent("big", "B", capacity=4)
    small.assign_task("T1")
    big.assign_task("T2")
    assert LeastLoadedPolicy().select([small, big], Task("T3", "x")).agent_id == "big"
