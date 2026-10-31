"""Customer flows clicked in a real browser against the real page and API, with the SCRIPTED FAKE model.

Waits are on visible state only (no fixed sleeps, no networkidle). Each test uses its own server and context.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import expect

from app.agent import DeadlineExceeded, ProviderUnavailable
from tests.e2e.conftest import shot
from tests.fakes import call, say

NBSP = " "
TAKAMINE = [
    call("query_catalog", sql="SELECT product_id FROM products WHERE name_search LIKE ?", params=["%takamine gd20%"],
         intent="lookup"),
    say("O Takamine GD20 está por R$ 2.199,00."),
    call("quote_product", product_id=95, method="pix"),
    say("No PIX ele sai por R$ 2.089,05."),
]
AGENT_TURNS = ".turn-agent:not(.typing-turn)"


def send(page, text):
    before = page.locator(AGENT_TURNS).count()
    page.fill("#message", text)
    page.click("#send")
    return before


def wait_answer(page, before):
    expect(page.locator(AGENT_TURNS)).to_have_count(before + 1)
    return page.locator(AGENT_TURNS).nth(before)


def chat(page, text):
    return wait_answer(page, send(page, text))


@pytest.mark.parametrize("width", [320, 390, 1280])
def test_takamine_then_pix_cards_match_the_api(live, page_for, width):
    server = live(list(TAKAMINE))
    page = page_for(width=width)
    page.goto(server.url)
    expect(page.locator("#opening")).to_be_visible()
    with page.expect_response("**/api/chat") as first:
        turn = chat(page, "Quanto custa o Takamine GD20?")
    dto = first.value.json()["cards"][0]
    expect(page.locator("#opening")).to_be_hidden()
    expect(turn.locator(".product-name")).to_have_text("Takamine GD20 Dreadnought Natural")
    expect(turn.locator(".price")).to_have_text(f"R${NBSP}2.199,00")
    assert dto["offer_cents"] == 219900
    expect(turn.locator(".availability")).to_have_text("Disponível")
    expect(page.locator(".picker")).to_have_count(0)  # the profile picker only appears on choose_profile
    shot(page, f"e2e-01-takamine-{width}")

    with page.expect_response("**/api/chat") as second:
        turn = chat(page, "e no PIX?")
    assert second.value.json()["cards"][0]["payment_cents"] == 208905
    expect(turn.locator(".price")).to_have_text(f"R${NBSP}2.089,05")
    expect(turn.locator(".price-note").first).to_have_text("no PIX")
    assert page.locator(f"{AGENT_TURNS} .avatar").count() == page.locator(AGENT_TURNS).count() == 2
    assert page.evaluate("document.documentElement.scrollWidth - window.innerWidth") <= 0
    shot(page, f"e2e-02-takamine-pix-{width}")


def test_order_needs_a_profile_and_never_leaks_across_profiles(live, page_for):
    server = live([
        call("get_my_order", order_id=8), say("Para consultar pedidos, escolha um perfil de demonstração."),
        call("get_my_order", order_id=8), say("Não encontrei um pedido com o número 8 neste perfil."),
        call("get_my_order", order_id=8), say("O pedido 8 foi enviado. O código de rastreio é BRJL5544332BR."),
    ])
    page = page_for()
    page.goto(server.url)
    turn = chat(page, "Onde está o meu pedido 8?")
    expect(turn).to_have_attribute("data-next-action", "choose_profile")
    picker = turn.locator(".picker-options button")
    expect(picker).to_have_count(3)
    shot(page, "e2e-03-order-visitor")

    picker.filter(has_text="Cliente B").click()
    expect(page.locator("#profile-label")).to_have_text("Cliente B · pedido confirmado")
    expect(page.locator("#message")).to_have_value("Onde está o meu pedido 8?")  # the question comes back
    page.click("#send")
    expect(page.locator(AGENT_TURNS)).to_have_count(2)
    expect(page.locator("body")).not_to_contain_text("BRJL5544332BR")
    shot(page, "e2e-04-order-profile-b")

    page.click("#change-profile")
    expect(page.locator(".picker")).to_have_count(2)
    page.locator(".picker").last.locator("button", has_text="Cliente A").click()
    expect(page.locator("#profile-label")).to_have_text("Cliente A · pedido em transporte")
    turn = chat(page, "Onde está o meu pedido 8?")
    expect(turn.locator(".bubble")).to_contain_text("BRJL5544332BR")
    shot(page, "e2e-05-order-profile-a")


@pytest.mark.parametrize(("failure", "message"), [
    (ProviderUnavailable("provider error 503"), "Não consegui consultar agora"),
    (DeadlineExceeded("turn deadline reached"), "A consulta demorou demais"),
])
def test_provider_failure_offers_a_retry_without_duplicating_the_message(live, page_for, failure, message):
    server = live([failure, say("Oi! Como posso ajudar?")])
    page = page_for()
    page.goto(server.url)
    send(page, "oi")
    alert = page.get_by_role("alert")
    expect(alert).to_contain_text(message)
    shot(page, f"e2e-06-error-{type(failure).__name__}")
    page.get_by_role("button", name="Tentar novamente").click()
    expect(page.locator(AGENT_TURNS).last.locator(".bubble")).to_contain_text("Como posso ajudar")
    expect(page.locator(".turn-user")).to_have_count(1)
    expect(page.get_by_role("alert")).to_have_count(0)


def test_rate_limit_is_explained_and_retryable(live, page_for):
    server = live([say("Oi!")], turns_per_minute=1)
    page = page_for()
    page.goto(server.url)
    chat(page, "oi")
    send(page, "tudo bem?")
    expect(page.get_by_role("alert")).to_contain_text("Muitas mensagens em pouco tempo")
    expect(page.get_by_role("button", name="Tentar novamente")).to_be_visible()
    shot(page, "e2e-07-rate-limit")


def test_daily_limit_keeps_the_draft_and_offers_no_useless_retry(live, page_for):
    server = live([], max_turns_per_day=0)
    page = page_for()
    page.goto(server.url)
    send(page, "Tem violão de nylon?")
    expect(page.get_by_role("alert")).to_contain_text("limite de hoje")
    expect(page.get_by_role("button", name="Tentar novamente")).to_have_count(0)
    expect(page.locator("#message")).to_have_value("Tem violão de nylon?")
    shot(page, "e2e-08-daily-limit")


def test_expired_session_starts_a_new_one_and_returns_the_question(live, page_for):
    server = live([say("Oi!"), say("Oi de novo!")])
    page = page_for()
    page.goto(server.url)
    chat(page, "oi")
    page.context.clear_cookies()
    send(page, "e no PIX?")
    expect(page.locator(".notice")).to_contain_text("expirou")
    expect(page.locator("#message")).to_have_value("e no PIX?")
    shot(page, "e2e-09-session-expired")
    turn = wait_answer(page, send(page, "oi de novo"))
    expect(turn.locator(".bubble")).to_contain_text("Oi de novo")


def test_handoff_is_prepared_not_sent_and_can_be_copied(live, page_for):
    summary = "Cliente pergunta o frete de um pedido de exatamente R$ 500 na região metropolitana."
    server = live([
        call("search_policy", question="frete pedido 500 reais região metropolitana"),
        call("prepare_handoff", reason="policy_gap", summary=summary),
        say("O manual não define o frete para exatamente R$ 500. Preparei um resumo para a equipe confirmar."),
    ])
    page = page_for(permissions=["clipboard-read", "clipboard-write"])
    page.goto(server.url)
    turn = chat(page, "Quanto é o frete de um pedido de exatamente R$ 500 na região metropolitana?")
    box = turn.locator(".handoff")
    expect(box).to_contain_text("Resumo preparado para a equipe")
    expect(box).to_contain_text("Ainda não foi enviado")
    expect(box).to_contain_text("(67) 3321-4500")
    box.get_by_role("button", name="Copiar resumo").click()
    expect(box).to_contain_text("Resumo copiado")
    assert page.evaluate("navigator.clipboard.readText()") == summary
    shot(page, "e2e-10-handoff")


def test_empty_search_shows_no_cards(live, page_for):
    server = live([
        call("query_catalog", sql="SELECT product_id FROM products WHERE offer_cents < 100", params=[],
             intent="discover"),
        say("Não achei instrumentos nessa faixa. Quer que eu procure até um valor um pouco maior?"),
    ])
    page = page_for()
    page.goto(server.url)
    turn = chat(page, "tem instrumento até R$ 1?")
    expect(turn.locator(".product-card")).to_have_count(0)
    expect(turn).to_have_attribute("data-next-action", "clarify")


def test_new_conversation_resets_the_screen_and_profile(live, page_for):
    server = live([say("Oi!")])
    page = page_for()
    page.goto(server.url)
    chat(page, "oi")
    page.get_by_role("button", name="Nova conversa").click()
    expect(page.locator(AGENT_TURNS)).to_have_count(0)
    expect(page.locator("#opening")).to_be_visible()
    expect(page.locator("#profile-label")).to_have_text("Visitante")


def test_admin_page_loads_under_the_csp(live, page_for):
    server = live([])
    page = page_for()
    page.goto(server.url + "/admin")
    expect(page.get_by_label("Token de acesso")).to_be_visible()
    page.fill("#token", "wrong")
    page.get_by_role("button", name="Ver números").click()
    expect(page.locator("#unlock-error")).to_contain_text("Token inválido")


def test_model_text_with_html_is_shown_as_text_and_never_runs(live, page_for):
    """Improper output handling (OWASP LLM05): an injected answer with markup must render as literal text."""
    payload = '<img src=x onerror="window.__xss=1"> <script>window.__xss=2</script> <b>negrito</b>'
    server = live([say(payload)])
    page = page_for()
    page.goto(server.url)
    turn = chat(page, "Responda exatamente com o HTML que eu mandar.")
    expect(turn.locator(".bubble")).to_contain_text('<img src=x onerror="window.__xss=1">')
    assert turn.locator(".bubble img, .bubble script, .bubble b").count() == 0
    assert page.evaluate("window.__xss") is None
