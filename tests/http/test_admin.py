"""/admin (D20) with a SCRIPTED FAKE model: token guard, aggregates computed by hand, and no customer text kept."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from tests.fakes import FakeLLM, call, say
from tests.http.test_chat_api import TAKAMINE_SQL, chat

TOKEN = "test-admin-token-not-a-secret"
SENTINEL = "SENTINELA-7Q"
NYLON_SQL = ("SELECT product_id FROM products WHERE category_id = 5 AND json_extract(specs, '$.strings') = 'nylon' "
             "AND availability = 'available' ORDER BY offer_cents")


@pytest.fixture
def admin_settings(settings, tmp_path):
    prices = tmp_path / "pricing.json"
    prices.write_text(json.dumps({"checked_on": "2026-10-31",
                                  "models": {"fake-scripted": {"input_per_mtok": 1.0, "output_per_mtok": 2.0}}}))
    return replace(settings, admin_token=TOKEN, pricing_path=prices)


def three_turns(admin_settings):
    llm = FakeLLM([
        call("query_catalog", sql=TAKAMINE_SQL, params=["%takamine gd20%"], intent="lookup"),
        say("O Takamine GD20 está por R$ 2.199,00."),
        call("quote_product", product_id=95, method="pix"),
        say("No PIX ele sai por R$ 2.089,05."),
        call("query_catalog", sql=NYLON_SQL, params=[], intent="discover"),
        say("Separei alguns violões de nylon."),
    ])
    app = create_app(admin_settings, llm=llm)
    client = TestClient(app)
    client.post("/api/session")
    for message in [f"{SENTINEL} quanto custa o Takamine GD20?", "e no PIX?", "tem violão de nylon?"]:
        assert chat(client, message).status_code == 200
    return client, app


def stats(client, token=TOKEN):
    headers = {"X-Admin-Token": token} if token is not None else {}
    return client.get("/admin/api/stats", headers=headers)


def test_stats_need_the_token(admin_settings):
    client, _ = three_turns(admin_settings)
    for token in (None, "", "wrong-token"):
        r = stats(client, token)
        assert r.status_code == 404 and r.json() == {"detail": "Not Found"}  # same body as a missing route
    assert stats(client).status_code == 200


def test_no_token_configured_means_always_404(settings):
    client = TestClient(create_app(replace(settings, admin_token=""), llm=FakeLLM([])))
    assert stats(client, None).status_code == 404
    assert stats(client, "").status_code == 404


def test_aggregates_match_hand_computation(admin_settings):
    client, _ = three_turns(admin_settings)
    s = stats(client).json()
    # Each turn: 2 fake model calls of 1 input + 1 output token -> 2 * 1.0 + 2 * 2.0 = 6 µUSD.
    assert s["turns"] == 3
    assert s["avg_cost_usd_per_answer"] == pytest.approx(6e-6)
    assert s["total_cost_usd"] == pytest.approx(18e-6)
    assert {t["topic"]: t["turns"] for t in s["topics"]} == {"Busca no catálogo": 2, "Preço no PIX": 1}
    top = s["top_products"]
    assert len(top) == 3  # the nylon turn shows 3 cards: 4 distinct products in total, only 3 are listed
    assert top[0] == {"product_id": 95, "name": "Takamine GD20 Dreadnought Natural", "times_shown": 2}
    assert s["price_checked_on"] == "2026-10-31" and s["since"]


def test_customer_text_is_never_kept(admin_settings):
    client, app = three_turns(admin_settings)
    assert SENTINEL not in json.dumps(stats(client).json(), ensure_ascii=False)
    assert SENTINEL not in repr(vars(app.state.metrics))


def test_missing_price_is_unavailable_not_zero(settings, tmp_path):
    client = TestClient(create_app(replace(settings, admin_token=TOKEN, pricing_path=tmp_path / "none.json"),
                                   llm=FakeLLM([say("Oi! Como posso ajudar?")])))
    client.post("/api/session")
    chat(client, "oi")
    s = stats(client).json()
    assert s["cost_available"] is False and s["avg_cost_usd_per_answer"] is None and s["turns"] == 1


def test_admin_page_is_a_shell_and_not_linked(admin_settings):
    client = TestClient(create_app(admin_settings, llm=FakeLLM([])))
    page = client.get("/admin")
    assert page.status_code == 200 and page.headers["x-robots-tag"] == "noindex"
    assert "Token de acesso" in page.text and "Busca no catálogo" not in page.text
    assert "/admin" not in client.get("/").text
