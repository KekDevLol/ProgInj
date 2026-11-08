import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_control import ApiModelAgent, DummyAgent, LocalModelAgent, Orchestrator


@pytest.fixture
def orc():
    o = Orchestrator()
    o.register_agent(DummyAgent("d1", "Dummy One", ["text", "code"], capacity=2))
    o.register_agent(DummyAgent("d2", "Dummy Two", ["text"], capacity=1))
    o.register_agent(LocalModelAgent("l1", "Llama", ["code"], model_path="D:/models/llama"))
    o.register_agent(ApiModelAgent("a1", "Cloud", ["text"], base_url="https://api.test", api_key_env="KEY"))
    return o


@pytest.fixture
def empty_orc():
    return Orchestrator()
