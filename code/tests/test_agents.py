import pytest

from agent_control import Agent, ApiModelAgent, DummyAgent, LocalModelAgent
from agent_control.exceptions import AgentNotConnectedError


def test_agent_is_abstract():
    with pytest.raises(TypeError):
        Agent("x", "y")


def test_create_local_agent():
    a = LocalModelAgent("l1", "Llama", ["Code", " TEXT "], capacity=2, model_path="D:/m", device="cuda")
    assert a.capabilities == {"code", "text"}
    assert (a.capacity, a.device) == (2, "cuda")
    assert a.get_type() == "Локальная модель"


def test_create_api_agent():
    a = ApiModelAgent("a1", "Cloud", base_url="https://x", api_key_env="KEY")
    assert a.get_type() == "API-агент"
    assert "api_key" not in a.to_dict()


@pytest.mark.parametrize("agent_id, name", [("", "n"), ("id", ""), ("   ", "n"), ("id", "   ")])
def test_empty_or_blank_id_or_name_rejected(agent_id, name):
    with pytest.raises(ValueError):
        DummyAgent(agent_id, name)


@pytest.mark.parametrize("capacity", [0, -1])
def test_capacity_below_one_rejected(capacity):
    with pytest.raises(ValueError):
        DummyAgent("d", "D", capacity=capacity)


def test_load_and_capacity():
    a = DummyAgent("d", "D", capacity=1)
    assert a.has_capacity
    a.assign_task("T1")
    assert a.load == 1 and not a.has_capacity
    a.active_tasks.append("hack")
    assert a.load == 1


@pytest.mark.parametrize("agent", [LocalModelAgent("l", "L"), ApiModelAgent("a", "A")])
def test_unconnected_agent_raises(agent):
    with pytest.raises(AgentNotConnectedError):
        agent.execute("hi")


def test_attach_runner():
    a = ApiModelAgent("a", "A")
    a.attach_runner(str.upper)
    assert a.execute("abc") == "ABC"
