import pytest

from agent_control import Agent, ApiModelAgent, DummyAgent, LocalModelAgent
from agent_control.exceptions import AgentNotConnectedError


def test_agent_is_abstract():
    with pytest.raises(TypeError):
        Agent("x", "y")


def test_create_local_agent():
    a = LocalModelAgent("l1", "Llama", ["Code", " TEXT "], capacity=2, model_path="D:/m", device="cuda")
    assert a.agent_id == "l1"
    assert a.capabilities == {"code", "text"}
    assert (a.capacity, a.device, a.model_path) == (2, "cuda", "D:/m")
    assert a.get_type() == "Локальная модель"


def test_create_api_agent():
    a = ApiModelAgent("a1", "Cloud", base_url="https://x", api_key_env="KEY")
    assert a.get_type() == "API-агент"
    assert a.api_key_env == "KEY"
    assert a.timeout_s == 60.0


@pytest.mark.parametrize("agent_id, name", [("", "name"), ("id", ""), ("", "")])
def test_empty_id_or_name_rejected(agent_id, name):
    with pytest.raises(ValueError):
        DummyAgent(agent_id, name)


@pytest.mark.parametrize("agent_id, name", [("   ", "name"), ("id", "   ")])
def test_blank_id_or_name_rejected(agent_id, name):
    with pytest.raises(ValueError):
        DummyAgent(agent_id, name)


@pytest.mark.parametrize("capacity", [0, -1])
def test_capacity_below_one_rejected(capacity):
    with pytest.raises(ValueError):
        DummyAgent("d", "D", capacity=capacity)


def test_minimal_capacity_ok():
    assert DummyAgent("d", "D", capacity=1).has_capacity


def test_load_and_capacity():
    a = DummyAgent("d", "D", capacity=2)
    a.assign_task("T1")
    assert a.load == 1 and a.has_capacity
    a.assign_task("T2")
    assert a.load == 2 and not a.has_capacity
    a.finish_task("T1")
    assert a.has_capacity


def test_active_tasks_returns_copy():
    a = DummyAgent("d", "D")
    a.active_tasks.append("hack")
    assert a.load == 0


@pytest.mark.parametrize("cap, expected", [("code", True), ("CODE", True), (" code ", True),
                                           ("", True), ("vision", False)])
def test_can_handle(cap, expected):
    assert DummyAgent("d", "D", ["code"]).can_handle(cap) is expected


def test_dummy_executes():
    assert "привет" in DummyAgent("d", "D").execute("привет")


@pytest.mark.parametrize("agent", [LocalModelAgent("l", "L"), ApiModelAgent("a", "A")])
def test_unconnected_agent_raises(agent):
    with pytest.raises(AgentNotConnectedError):
        agent.execute("hi")


def test_attach_runner():
    a = ApiModelAgent("a", "A")
    a.attach_runner(str.upper)
    assert a.is_connected
    assert a.execute("abc") == "ABC"


def test_to_dict_has_no_secrets():
    a = ApiModelAgent("a", "A", base_url="https://x", api_key_env="MY_KEY")
    a.attach_runner(lambda p: p)
    data = a.to_dict()
    assert data["api_key_env"] == "MY_KEY"
    assert "api_key" not in data
