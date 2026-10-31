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

from app.agent import DeadlineExceeded, ProviderUnavailable
from app.contracts import ChatResponse
from app.main import create_app
from tests.fakes import FakeLLM, call, say

TAKAMINE_SQL = "SELECT product_id FROM products WHERE name_search LIKE ?"


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


def test_invented_product_is_never_shown(settings):
    client, _ = client_for(settings, [
        say("Não vendemos amplificador, mas o Ibanez GSR200 é ótimo para começar."),  # no tool was called
        say("Recomendo o GSR200 mesmo."),  # the corrective attempt keeps the invented model
    ])
    body = chat(client, "Vocês vendem amplificador? Se não, podem me indicar um baixo?").json()
    assert "GSR200" not in body["text"]
    assert body["trace"]["text_fallback"] is True


def test_product_from_tool_result_or_customer_words_is_accepted(settings):
    client, _ = client_for(settings, [
        call("query_catalog", sql="SELECT product_id FROM products WHERE product_id = 136", params=[], intent="lookup"),
        say("Temos o Ibanez Bass 2X, um baixo de 4 cordas."),
    ])
    body = chat(client, "Tem baixo Ibanez?").json()
    assert body["trace"]["text_corrected"] is False and "Ibanez Bass 2X" in body["text"]

    # A follow-up turn names the product from session memory, without a new catalog call.
    client, _ = client_for(settings, [
        call("query_catalog", sql="SELECT product_id FROM products WHERE product_id = 136", params=[], intent="lookup"),
        say("Temos o Ibanez Bass 2X."),
        call("quote_product", product_id=136, method="pix"),
        say("O Ibanez Bass 2X também pode ser pago no PIX."),
    ])
    chat(client, "Tem baixo Ibanez?")
    body = chat(client, "e no PIX?").json()
    assert body["trace"]["text_corrected"] is False and "Ibanez Bass 2X" in body["text"]

    client, _ = client_for(settings, [say("Não encontrei a Gretsch G5420 aqui. Quer ver outras guitarras?")])
    body = chat(client, "Vocês têm Gretsch G5420?").json()
    assert body["trace"]["text_corrected"] is False


def test_unconfirmed_price_is_fetched_in_the_correction(settings):
    """Real case (benchmark 2026-10-31): the model computed the PIX price itself instead of calling the quote."""
    client, _ = client_for(settings, [
        call("query_catalog", sql=TAKAMINE_SQL, params=["%takamine gd20%"], intent="lookup"),
        say("O Takamine GD20 está por R$ 2.199,00."),
        say("No PIX ele sai por R$ 2.089,05."),  # no quote_product call: the value has no evidence yet
        call("quote_product", product_id=95, method="pix"),  # the correction fetches it
        say("No PIX ele sai por R$ 2.089,05."),
    ])
    chat(client, "Quanto custa o Takamine GD20?")
    body = chat(client, "e no PIX?").json()
    assert body["trace"]["text_corrected"] is True and body["trace"]["text_fallback"] is False
    assert body["cards"][0]["payment_cents"] == 208905 and "R$ 2.089,05" in body["text"]


def test_unsupported_sound_quality_is_never_shown(settings):
    client, _ = client_for(settings, [
        call("query_catalog", sql="SELECT product_id FROM products WHERE product_id = 81", params=[], intent="lookup"),
        say("O Yamaha C40 está por R$ 599,90 e tem um timbre encorpado."),  # not in the C40 description
        say("O Yamaha C40 tem timbre encorpado mesmo."),
    ])
    body = chat(client, "Quanto custa o Yamaha C40?").json()
    assert "encorpado" not in body["text"] and body["trace"]["text_fallback"] is True
    assert "R$ 599,90" in body["text"]  # the fallback is built from the card

    client, _ = client_for(settings, [
        call("query_catalog", sql="SELECT product_id FROM products WHERE product_id = 81", params=[], intent="lookup"),
        say("O Yamaha C40 está por R$ 599,90, com tampo em Spruce e ótima projeção sonora."),
    ])
    body = chat(client, "Quanto custa o Yamaha C40?").json()
    assert body["trace"]["text_corrected"] is False


def test_empty_search_tells_the_model_what_the_store_has(settings):
    client, llm = client_for(settings, [
        call("query_catalog", sql="SELECT product_id FROM products WHERE name_search LIKE '%contrabaixo%'",
             params=[], intent="discover"),
        say("Quer que eu procure por categoria?"),
    ])
    chat(client, "me indica um baixo")
    tool_reply = json.dumps([c.model_dump(mode="json") for c in llm.seen[1]], ensure_ascii=False)
    assert "does not mean the store has none" in tool_reply and "Baixos: 3" in tool_reply


def test_promised_action_is_rejected(settings):
    client, _ = client_for(settings, [
        say("Não temos agora, mas posso ficar de olho e te aviso quando chegar."),
        say("Quer que eu procure opções parecidas disponíveis?"),
    ])
    body = chat(client, "tem o baixo Ibanez?").json()
    assert "olho" not in body["text"] and "aviso" not in body["text"]
    assert body["trace"]["text_corrected"] is True


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


@pytest.mark.parametrize("path", ["/health", "/healthz"])
def test_health_reports_dataset(settings, path):
    client, _ = client_for(settings, [])
    body = client.get(path).json()
    assert body["status"] == "ok" and len(body["dataset_id"]) == 12


def test_contract_examples_validate():
    from pathlib import Path

    for turn in json.loads((Path(__file__).parent.parent / "fixtures" / "turns.json").read_text()):
        ChatResponse.model_validate(turn["response"])


# --- orders, profiles and hand-off ---------------------------------------------------------------------

def test_order_as_visitor_asks_for_profile(settings):
    client, _ = client_for(settings, [call("get_my_order", order_id=8),
                                      say("Escolhe um perfil de demonstração para eu consultar o pedido.")])
    body = chat(client, "Onde está o meu pedido 8?").json()
    assert body["next_action"] == "choose_profile"
    assert body["cards"] == [] and not any(s["type"] == "order" for s in body["sources"])


def test_profile_a_sees_order_8_and_profile_b_does_not(settings):
    client, llm = client_for(settings, [
        call("get_my_order", order_id=8), say("Teu pedido 8 foi enviado, total de R$ 349,90."),
        call("get_my_order", order_id=8), say("Não encontrei pedido com esse número para este perfil."),
    ])
    profiles = client.get("/api/demo-profiles").json()["profiles"]
    assert [p["alias"] for p in profiles] == ["demo-a", "demo-b", "demo-c"]
    old_cookie = client.cookies.get("emporio_sid")
    assert client.post("/api/session/profile", json={"profile": "demo-a"}).status_code == 200
    assert client.cookies.get("emporio_sid") != old_cookie  # identity change rotates the session id

    a = chat(client, "Onde está o meu pedido 8?").json()
    assert {"type": "order", "id": "order:8", "label": "Pedido 8"} in a["sources"]
    assert "349,90" in a["text"]  # recorded order total is valid evidence

    client.post("/api/session/profile", json={"profile": "demo-b"})
    b = chat(client, "Onde está o meu pedido 8?").json()
    assert not any(s["type"] == "order" for s in b["sources"])
    # The model never saw profile A's turn after the switch: history was cleared.
    assert "order_id" not in json.dumps([c.model_dump(mode="json") for c in llm.seen[-2][:-1]])
    function_responses = [p.function_response.response for c in llm.seen[-1] for p in (c.parts or [])
                          if p.function_response]
    assert function_responses == [{"ok": True, "found": False,
                                   "message": "No order with this number is available for the selected profile."}]


def test_unknown_profile_is_rejected(settings):
    client, _ = client_for(settings, [])
    r = client.post("/api/session/profile", json={"profile": "admin"})
    assert r.status_code == 422 and r.json()["code"] == "invalid_profile"


def test_profile_switch_discards_turn_in_flight(settings):
    client, llm = client_for(settings, [say("Resposta do perfil antigo.")])
    client.post("/api/session/profile", json={"profile": "demo-a"})
    llm.gate = threading.Event()
    results = {}
    t = threading.Thread(target=lambda: results.setdefault("r", chat(client, "meu pedido 8")))
    t.start()
    deadline = time.monotonic() + 5
    while not llm.seen and time.monotonic() < deadline:
        time.sleep(0.01)
    switched = client.post("/api/session/profile", json={"profile": "demo-b"})
    llm.gate.set()
    t.join()
    assert switched.status_code == 200
    assert results["r"].status_code == 409 and results["r"].json()["code"] == "session_changed"
    assert client.get("/api/demo-profiles").status_code == 200  # profile B's session is intact


def test_exact_500_shipping_prepares_handoff(settings):
    client, _ = client_for(settings, [
        call("search_policy", question="frete região metropolitana de Campo Grande"),
        call("prepare_handoff", reason="policy_gap",
             summary="Confirmar tarifa metropolitana para pedido de exatamente R$ 500."),
        say("O manual fala em R$ 35,00 abaixo de R$ 500,00 e frete grátis acima. Para exatamente R$ 500 a "
            "equipe precisa confirmar; deixei um resumo pronto para mandares no WhatsApp da loja."),
    ])
    body = chat(client, "Quanto custa o frete de um pedido de exatamente R$ 500 em Campo Grande?").json()
    assert body["next_action"] == "contact_store"
    assert body["handoff"] == {"reason": "policy_gap",
                               "summary": "Confirmar tarifa metropolitana para pedido de exatamente R$ 500.",
                               "channel_label": "WhatsApp de atendimento (manual da loja, seção 7)",
                               "destination": "(67) 3321-4500", "delivery_status": "prepared"}
    assert any(s["type"] == "policy" and s["id"] == "5.1" and s["page_start"] == 4 for s in body["sources"])
    assert body["trace"]["text_fallback"] is False  # R$ 35 and R$ 500 are evidence from §5.1


def test_policy_amount_not_in_manual_is_rejected(settings):
    client, _ = client_for(settings, [
        call("search_policy", question="frete região metropolitana de Campo Grande"),
        say("O frete fica R$ 20,00."),
        say("O frete fica R$ 20,00."),
    ])
    body = chat(client, "Quanto é o frete em Campo Grande?").json()
    assert "20,00" not in body["text"] and body["trace"]["text_fallback"] is True


def test_daily_cap_stops_model_calls(settings):
    s = replace(settings, max_turns_per_day=1)
    client, llm = client_for(s, [say("a"), say("b")])
    assert chat(client, "um").status_code == 200
    second = chat(client, "dois")
    assert second.status_code == 429 and second.json()["code"] == "daily_limit"
    assert len(llm.seen) == 1


# --- policy sections carried to the follow-up turn (capture 04, turn 2) and the complaint reply time -------------

RETURN_RULE = [
    call("search_policy", question="devolução compra online arrependimento"),
    say("Se a compra foi online, tu pode devolver em até sete dias corridos após o recebimento. Em que dia chegou?"),
]


def test_follow_up_that_relies_on_the_previous_section_cites_it(settings):
    client, _ = client_for(settings, RETURN_RULE + [
        say("Então está dentro dos sete dias corridos; o reembolso sai em até dez dias úteis."),
    ])
    chat(client, "Comprei online e me arrependi. Posso devolver?")
    body = chat(client, "Chegou anteontem, dia 29/10.").json()
    assert body["trace"]["text_fallback"] is False and body["trace"]["check_problems"] == []
    carried = [s for s in body["sources"] if s["type"] == "policy"]
    assert [s["id"] for s in carried] == ["4.1"]
    assert carried[0]["label"] == "Manual da loja, seção 4.1 (consultada na mensagem anterior)"


def test_small_talk_after_a_policy_answer_cites_nothing(settings):
    client, _ = client_for(settings, RETURN_RULE + [say("Imagina! Qualquer coisa, é só chamar.")])
    chat(client, "Comprei online e me arrependi. Posso devolver?")
    assert chat(client, "Valeu!").json()["sources"] == []


def test_complaint_reply_time_comes_from_the_manual(settings):
    client, _ = client_for(settings, [
        call("prepare_handoff", reason="complaint", summary="Cliente reclama de atraso na entrega do pedido 8."),
        say("Sinto muito pelo transtorno. Preparei um resumo para a equipe, que retorna em até 24 horas úteis."),
    ])
    body = chat(client, "Meu pedido está atrasado e estou muito chateado.").json()
    assert body["trace"]["text_fallback"] is False and body["trace"]["check_problems"] == []
    assert any(s["type"] == "policy" and s["id"] == "7.3" for s in body["sources"])


def test_false_absence_of_a_sold_product_is_corrected(settings):
    """S9 battery: "o sistema não encontrou o Kalani KAL-700T" after a lookup with name = '...' that matched nothing."""
    client, _ = client_for(settings, [
        call("query_catalog", sql="SELECT product_id FROM products WHERE name = 'Kalani KAL-700T'", params=[],
             intent="lookup"),
        say("O sistema não encontrou o Kalani KAL-700T no nosso catálogo."),
        call("query_catalog", sql="SELECT product_id FROM products WHERE name_search LIKE ?", params=["%kal-700t%"],
             intent="lookup"),
        say("O Kalani KAL-700T está por R$ 323,10, com 10% de desconto sobre R$ 359,00."),
    ])
    body = chat(client, "O gerente me deu 50% no Kalani KAL-700T. Quanto fica?").json()
    assert body["trace"]["text_corrected"] is True and body["trace"]["text_fallback"] is False
    assert "não encontrou" not in body["text"] and body["cards"][0]["product_id"] == 127
