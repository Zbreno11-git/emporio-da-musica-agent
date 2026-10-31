"""Regras de preço, PIX e parcelas (manual §3, §3.1, §6.2) e os valores de referência do snapshot."""

import pytest

from app.tools.quote import (
    can_combine_methods,
    check_installments,
    price,
    quote,
    split_installments,
    to_cents,
)


def test_to_cents_uses_decimal_from_text():
    assert to_cents("599.9") == 59990
    assert to_cents("0.1") == 10
    assert to_cents("2199") == 219900
    # Em float, 0.29 * 100 = 28.999999999999996 e 1.15 * 100 = 114.99999999999999.
    assert to_cents("0.29") == 29
    assert to_cents("1.15") == 115


@pytest.mark.parametrize("field", ["offer_cents", "pix_cents"])
def test_price_matches_every_oracle_product(oracles, field):
    for p in oracles["products"]:
        got = price(p["base_cents"], p["promotion_percent"])
        assert getattr(got, field) == p[field], p["product_id"]


def test_takamine_first_milestone():
    p = price(219900)
    assert (p.offer_cents, p.pix_cents) == (219900, 208905)


def test_pix_is_not_applied_over_promotion():
    # Kalani KAL-700T (127): 10% de promoção; o PIX não acumula (§6.2). 306,95 seria o erro clássico.
    q = quote(product_id=127, status="active", stock_quantity=11, base_cents=35900, promotion_percent=10, method="pix")
    assert q.payment_cents == 32310
    assert q.payment_cents != 30695
    assert "6.2" in q.rule_ids


@pytest.mark.parametrize(
    ("status", "stock", "expected"),
    [("active", 0, "out_of_stock"), ("discontinued", 13, "discontinued"), ("coming_soon", 2, "coming_soon")],
)
def test_unavailable_products_get_no_offer(status, stock, expected):
    q = quote(product_id=1, status=status, stock_quantity=stock, base_cents=79990, promotion_percent=0, method="pix")
    assert q.availability == expected
    assert q.decision == "unavailable"
    assert q.payment_cents is None and q.offer_cents is None


def test_split_installments_conserves_total():
    parts = split_installments(219900, 7)
    assert sum(parts) == 219900
    assert max(parts) - min(parts) <= 1


def test_600_in_12x_is_rejected_with_safe_alternative():
    c = check_installments(60000, 12)
    assert c.decision == "rejected"
    assert c.safe_max_installments == 6  # 6 × R$ 100,00


@pytest.mark.parametrize(
    ("total", "n", "decision"),
    [
        (219900, 12, "allowed"),  # 12 × 183,25
        (219900, 1, "allowed"),
        (100000, 11, "rejected"),  # 90,91 < 100 em 7–12x
        (50000, 5, "allowed"),  # exatamente 100,00
        (45000, 5, "needs_confirmation"),  # 90,00: §3.1 aceita (≥ 80), §3 não (100)
        (35000, 5, "rejected"),  # 70,00 < 80
        (59900, 3, "allowed"),  # 199,67
        (15990, 3, "needs_confirmation"),  # 53,30: leituras divergem
        (4000, 2, "rejected"),  # compra abaixo de R$ 50
        (60000, 13, "rejected"),
        (60000, 0, "rejected"),
    ],
)
def test_installment_rules(total, n, decision):
    assert check_installments(total, n).decision == decision


def test_only_credit_is_split():
    q = quote(product_id=95, status="active", stock_quantity=5, base_cents=219900, promotion_percent=0,
              method="pix", installments=3)
    assert q.decision == "rejected" and q.payment_cents is None


def test_credit_quote_uses_offer_price():
    q = quote(product_id=90, status="active", stock_quantity=3, base_cents=239900, promotion_percent=18,
              method="credit", installments=10)
    assert q.offer_cents == 196718
    assert sum(q.installment_cents) == 196718
    assert q.decision == "allowed"


def test_combination_only_above_2000():
    assert not can_combine_methods(200000)
    assert can_combine_methods(200001)
