"""Tests of the tool-calling loop with a fake Anthropic client (no API key)."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pytest

from emporio_agent.agent import TOOLS, Agent
from emporio_agent.config import STORE_TZ, Settings
from emporio_agent.data import load_store
from emporio_agent.policies import load_policy_index


@dataclass
class Block:
    type: str
    text: str = ""
    name: str = ""
    input: dict = field(default_factory=dict)
    id: str = ""

    def model_dump(self):
        return {k: v for k, v in self.__dict__.items() if v not in ("", {})}


@dataclass
class Response:
    stop_reason: str
    content: list


class FakeMessages:
    """Returns scripted responses in order and records every request."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.script.pop(0)


class FakeClient:
    def __init__(self, script):
        self.messages = FakeMessages(script)


@pytest.fixture(scope="module")
def store():
    return load_store()


@pytest.fixture(scope="module")
def index():
    return load_policy_index()


def make_agent(store, index, script, tmp_path):
    settings = Settings(
        model="fake-model",
        data_dir=Path("data"),
        now=datetime(2026, 3, 16, 10, 0, tzinfo=STORE_TZ),
        api_key="fake",
    )
    return Agent(settings, store, index, client=FakeClient(script), sessions_dir=tmp_path)


def test_tool_definitions_are_well_formed():
    names = {t["name"] for t in TOOLS}
    assert names == {"search_products", "product_details", "order_status", "store_status", "search_policy"}
    for t in TOOLS:
        assert t["description"]
        assert t["input_schema"]["type"] == "object"


def test_loop_runs_tool_then_answers(store, index, tmp_path):
    script = [
        Response("tool_use", [Block("tool_use", name="product_details", input={"name_or_id": "Takamine GD20"}, id="t1")]),
        Response("end_turn", [Block("text", text="O Takamine GD20 custa R$ 2.199,00.")]),
    ]
    agent = make_agent(store, index, script, tmp_path)
    reply = agent.chat("quanto custa o takamine gd20?")

    assert reply == "O Takamine GD20 custa R$ 2.199,00."
    # user, assistant(tool_use), user(tool_result), assistant(text)
    assert [m["role"] for m in agent.messages] == ["user", "assistant", "user", "assistant"]
    result = agent.messages[2]["content"][0]
    assert result["type"] == "tool_result" and result["tool_use_id"] == "t1"
    assert '"list_price_brl": 2199.0' in result["content"]
    # second request carried the tool result and the system prompt
    second = agent.client.messages.calls[1]
    assert second["system"].startswith("Você é o assistente virtual")
    assert second["tools"] is TOOLS


def test_system_prompt_has_store_time(store, index, tmp_path):
    agent = make_agent(store, index, [], tmp_path)
    assert "16/03/2026 10:00, segunda-feira. Loja aberta" in agent.system_prompt


def test_tool_error_becomes_is_error_result(store, index, tmp_path):
    script = [
        Response("tool_use", [Block("tool_use", name="order_status", input={"order_id": 1}, id="t1")]),
        Response("end_turn", [Block("text", text="Preciso do seu nome e e-mail.")]),
    ]
    agent = make_agent(store, index, script, tmp_path)
    agent.chat("pedido 1")
    result = agent.messages[2]["content"][0]
    assert result["is_error"] is True


def test_loop_stops_after_max_rounds(store, index, tmp_path):
    forever = Response("tool_use", [Block("tool_use", name="store_status", input={}, id="t")])
    agent = make_agent(store, index, [forever] * 10, tmp_path)
    reply = agent.chat("oi")
    assert "problema" in reply
    assert len(agent.client.messages.calls) == 6


def test_refusal_stop_reason(store, index, tmp_path):
    agent = make_agent(store, index, [Response("refusal", [])], tmp_path)
    reply = agent.chat("...")
    assert "não consigo ajudar" in reply


def test_session_is_saved_and_reloaded(store, index, tmp_path):
    script = [Response("end_turn", [Block("text", text="Oi! Como posso ajudar?")])]
    agent = make_agent(store, index, script, tmp_path)
    agent.chat("oi")
    path = tmp_path / f"{agent.session_id}.json"
    assert path.exists()

    other = make_agent(store, index, [], tmp_path)
    other.load(agent.session_id)
    assert other.transcript() == [("user", "oi"), ("assistant", "Oi! Como posso ajudar?")]
