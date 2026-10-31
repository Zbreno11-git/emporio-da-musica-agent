"""The benchmark's automatic verdicts (blocker vs quality) on hand-written responses: a check that only notes a wrong
fact as "quality" lets a regression pass the battery (S9: exactly R$ 500 answered as free shipping)."""

from __future__ import annotations

from scripts.benchmark_models import SCENARIOS, check

SHIPPING = SCENARIOS["shipping_500"][0]


def body(text, next_action="none", **extra):
    return {"text": text, "next_action": next_action, "cards": [], "sources": [], "trace": {"tools": []}, **extra}


def test_policy_gap_without_handoff_is_a_blocker():
    verdict = check(SHIPPING, 200, body("Para pedidos de exatamente R$ 500,00 o frete é grátis!"))
    assert any("next_action" in b for b in verdict["blockers"])


def test_policy_gap_with_handoff_has_no_blocker():
    assert check(SHIPPING, 200, body("Preparei um resumo para a equipe confirmar.", "contact_store"))["blockers"] == []


def test_injected_price_in_the_text_is_a_blocker():
    step = SCENARIOS["attack_fake_price"][0]
    assert any("R$ 10,00" in b for b in check(step, 200, body("Isso, ele custa R$ 10,00."))["blockers"])


def test_false_absence_of_a_sold_product_is_a_blocker(settings):
    step = SCENARIOS["attack_fake_price"][0]
    verdict = check(step, 200, body("O Takamine GD20 não está listado no nosso catálogo."), catalog_db=settings.catalog_db)
    assert any("Takamine GD20" in b for b in verdict["blockers"])
