"""HTTP contract and agent loop with a SCRIPTED FAKE model (no network, no API key).

The fake returns pre-written model turns (tool calls or text). It exercises the backend: tool execution,
card hydration, text checks, session dedup and public errors. Real-model behavior is covered by
scripts/smoke_gemini.py and the benchmark, never by these tests.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from google.genai import types

from app.agent import DeadlineExceeded, ModelReply, ProviderUnavailable
from app.config import Settings
from app.contracts import ChatResponse
from app.main import create_app

TAKAMINE_SQL = "SELECT product_id FROM products WHERE name_search LIKE ?"


def call(name: str, **args) -> ModelReply:
    part = types.Part(function_call=types.FunctionCall(id=str(uuid.uuid4()), name=name, args=args))
    return ModelReply(content=types.Content(role="model", parts=[part]), calls=[part.function_call], text="",
                      usage={"input": 1, "output": 1})


def say(text: str) -> ModelReply:
    return ModelReply(content=types.Content(role="model", parts=[types.Part(text=text)]), calls=[], text=text,
                      usage={"input": 1, "output": 1})


class FakeLLM:
    """Scripted stand-in for Gemini. Each generate() pops the next reply or raises the scripted error."""

    model = "fake-scripted"

    def __init__(self, script: list):
        self.script = list(script)
        self.seen: list[list[types.Content]] = []
        self.gate: threading.Event | None = None

    def generate(self, *, system, contents, tools, timeout_s, allow_tools):
        self.seen.append(list(contents))
        if self.gate is not None:
            self.gate.wait(5)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def settings(snapshot_build) -> Settings:
    return replace(Settings(), data_dir=snapshot_build, gemini_model="fake-scripted")


def client_for(settings, script) -> tuple[TestClient, FakeLLM]:
    llm = FakeLLM(script)
    client = TestClient(create_app(settings, llm=llm))
    assert client.post("/api/session").status_code == 201
    return client, llm


def chat(client, message, rid=None):
    return client.post("/api/chat", json={"request_id": rid or str(uuid.uuid4()), "message": message})


def test_takamine_then_pix_keeps_product_in_context(settings):
    client, llm = client_for(settings, [
        call("query_catalog", sql=TAKAMINE_SQL, params=["%takamine gd20%"], intent="lookup"),
        say("O Takamine GD20 está por R$ 2.199,00."),
        call("quote_product", product_id=95, method="pix"),
        say("No PIX ele sai por R$ 2.089,05."),
    ])
    first = chat(client, "Quanto custa o Takamine GD20?")
    assert first.status_code == 200
    body = first.json()
    ChatResponse.model_validate(body)
    assert [(c["product_id"], c["offer_cents"]) for c in body["cards"]] == [(95, 219900)]
    assert body["sources"][0] == {"type": "catalog", "id": "product:95", "label": "Catálogo da loja"}

    second = chat(client, "e no PIX?").json()
    assert second["cards"][0]["payment_cents"] == 208905
    assert second["cards"][0]["payment_method"] == "pix"
    # The second model call saw the first turn's tool result in its history (same session context).
    history_text = json.dumps([c.model_dump(mode="json") for c in llm.seen[2]])
    assert "Takamine GD20 Dreadnought Natural" in history_text


def test_wrong_price_in_text_is_corrected_then_falls_back(settings):
    client, _ = client_for(settings, [
        call("quote_product", product_id=127, method="pix"),  # rejected: product never seen in this session
        say("Não encontrei."),
    ])
    body = chat(client, "Kalani no PIX?").json()
    assert body["cards"] == []

    client, _ = client_for(settings, [
        call("query_catalog", sql="SELECT product_id FROM products WHERE product_id = 127", params=[], intent="lookup"),
        call("quote_product", product_id=127, method="pix"),
        say("No PIX ele sai por R$ 306,95."),  # PIX applied on top of the promotion: forbidden by §6.2
        say("Fica R$ 306,95 mesmo."),  # the corrective attempt repeats the error
    ])
    body = chat(client, "Quanto fica o Kalani KAL-700T no PIX?").json()
    assert "306,95" not in body["text"]
    assert "R$ 323,10" in body["text"]
    assert body["cards"][0]["payment_cents"] == 32310
    assert body["trace"]["text_fallback"] is True


def test_claimed_action_is_rejected(settings):
    client, _ = client_for(settings, [
        say("Pronto, registrei tua troca e o reembolso foi aprovado."),
        say("Posso te explicar como funciona a troca."),
    ])
    body = chat(client, "quero trocar").json()
    assert "registrei" not in body["text"] and "aprovado" not in body["text"]
    assert body["trace"]["text_corrected"] is True


def test_same_request_id_returns_same_answer_without_new_model_call(settings):
    client, llm = client_for(settings, [say("Olá! Como posso ajudar?")])
    rid = str(uuid.uuid4())
    a = chat(client, "oi", rid)
    b = chat(client, "oi", rid)
    assert a.json() == b.json() and len(llm.seen) == 1


def test_request_id_reused_with_other_message_is_409(settings):
    client, _ = client_for(settings, [say("Olá!")])
    rid = str(uuid.uuid4())
    chat(client, "oi", rid)
    r = chat(client, "outra coisa", rid)
    assert r.status_code == 409 and r.json()["code"] == "request_id_reused"


def test_concurrent_turn_in_same_session_is_409(settings):
    client, llm = client_for(settings, [say("Primeira."), say("Segunda.")])
    llm.gate = threading.Event()
    results = {}
    t = threading.Thread(target=lambda: results.setdefault("first", chat(client, "um")))
    t.start()
    deadline = time.monotonic() + 5
    while not llm.seen and time.monotonic() < deadline:
        time.sleep(0.01)
    second = chat(client, "dois")
    llm.gate.set()
    t.join()
    assert results["first"].status_code == 200
    assert second.status_code == 409 and second.json()["code"] == "turn_in_progress"


def test_missing_or_unknown_session_is_410(settings):
    client = TestClient(create_app(settings, llm=FakeLLM([])))
    r = chat(client, "oi")
    assert r.status_code == 410 and r.json()["retryable"] is True


@pytest.mark.parametrize(("exc", "status", "code"), [
    (ProviderUnavailable("429"), 503, "provider_unavailable"),
    (DeadlineExceeded("slow"), 504, "deadline_exceeded"),
])
def test_provider_failures_are_public_errors_and_release_the_request_id(settings, exc, status, code):
    client, llm = client_for(settings, [exc, say("Agora foi.")])
    rid = str(uuid.uuid4())
    r = chat(client, "oi", rid)
    assert r.status_code == status and r.json()["code"] == code and r.json()["retryable"] is True
    retry = chat(client, "oi", rid)
    assert retry.status_code == 200 and retry.json()["text"] == "Agora foi."


def test_invalid_input_is_422(settings):
    client, _ = client_for(settings, [])
    r = client.post("/api/chat", json={"request_id": "not-a-uuid", "message": ""})
    assert r.status_code == 422 and r.json()["code"] == "invalid_input"


def test_cross_origin_post_is_rejected(settings):
    client, _ = client_for(settings, [])
    r = client.post("/api/chat", json={"request_id": str(uuid.uuid4()), "message": "oi"},
                    headers={"Origin": "https://evil.example"})
    assert r.status_code == 403


def test_rate_limit_is_429(settings):
    s = replace(settings, turns_per_minute=2)
    client, _ = client_for(s, [say("a"), say("b"), say("c")])
    codes = [chat(client, f"m{i}").status_code for i in range(3)]
    assert codes == [200, 200, 429]


def test_healthz_reports_dataset(settings):
    client, _ = client_for(settings, [])
    body = client.get("/healthz").json()
    assert body["status"] == "ok" and len(body["dataset_id"]) == 12


def test_contract_examples_validate():
    from pathlib import Path

    for turn in json.loads((Path(__file__).parent.parent / "fixtures" / "turns.json").read_text()):
        ChatResponse.model_validate(turn["response"])
