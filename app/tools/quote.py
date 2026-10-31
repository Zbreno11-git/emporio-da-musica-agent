"""Preço, promoção, PIX e parcelas em centavos inteiros.

Regras do manual da loja (v2.1):
- §3: PIX tem 5% sobre o preço de tabela; crédito em até 12x sem juros com parcela mínima de R$ 100.
- §3.1: até 3x sem mínimo "exceto abaixo de R$ 50"; 4–6x mínimo R$ 80; 7–12x mínimo R$ 100;
  combinação de formas de pagamento só acima de R$ 2.000.
- §6.2: promoções não são cumulativas; o PIX não se aplica sobre preço promocional.

Onde §3 e §3.1 levam a resultados diferentes, a decisão é `needs_confirmation` e a função
oferece uma opção que vale em todas as leituras. O arredondamento é ROUND_HALF_UP, uma vez,
no valor final.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

PIX_DISCOUNT_PERCENT = 5
MAX_INSTALLMENTS = 12
GENERAL_MIN_INSTALLMENT_CENTS = 10_000  # §3 e §3.1 (7–12x)
MID_MIN_INSTALLMENT_CENTS = 8_000  # §3.1 (4–6x)
LOW_THRESHOLD_CENTS = 5_000  # §3.1 (até 3x, "exceto abaixo de R$ 50")
COMBINATION_MIN_CENTS = 200_000  # §3.1, "acima de R$ 2.000"

Method = Literal["table", "pix", "debit", "credit", "boleto"]
Availability = Literal["available", "out_of_stock", "discontinued", "coming_soon"]
Decision = Literal["allowed", "rejected", "needs_confirmation", "unavailable"]


def to_cents(value: str | Decimal) -> int:
    """Converte BRL textual ("599.9") em centavos, sem passar por float."""
    amount = Decimal(value) if isinstance(value, Decimal) else Decimal(str(value).strip())
    if amount < 0:
        raise ValueError(f"valor negativo: {value!r}")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _percent_of(cents: int, keep_percent: int) -> int:
    return int((Decimal(cents) * keep_percent / 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def availability(status: str, stock_quantity: int) -> Availability:
    if status == "discontinued":
        return "discontinued"
    if status == "coming_soon":
        return "coming_soon"
    if status == "active":
        return "available" if stock_quantity > 0 else "out_of_stock"
    raise ValueError(f"status desconhecido: {status!r}")


@dataclass(frozen=True)
class Pricing:
    base_cents: int
    promotion_percent: int
    offer_cents: int
    pix_cents: int


def price(base_cents: int, promotion_percent: int = 0) -> Pricing:
    """Preço vigente e PIX. Com promoção ativa, PIX = oferta (§6.2); sem promoção, 5% sobre a tabela (§3)."""
    if not 0 <= promotion_percent < 100:
        raise ValueError(f"percentual de promoção fora do intervalo: {promotion_percent}")
    offer = _percent_of(base_cents, 100 - promotion_percent) if promotion_percent else base_cents
    pix = offer if promotion_percent else _percent_of(base_cents, 100 - PIX_DISCOUNT_PERCENT)
    return Pricing(base_cents, promotion_percent, offer, pix)


def split_installments(total_cents: int, n: int) -> list[int]:
    """Reparte o total em n parcelas que somam exatamente o total (as primeiras levam o resto)."""
    q, r = divmod(total_cents, n)
    return [q + 1] * r + [q] * (n - r)


@dataclass(frozen=True)
class InstallmentCheck:
    decision: Decision
    rule_ids: list[str]
    reason: str
    safe_max_installments: int  # maior n válido em todas as leituras (1 = à vista)


def check_installments(total_cents: int, n: int) -> InstallmentCheck:
    if not 1 <= n <= MAX_INSTALLMENTS:
        return InstallmentCheck("rejected", ["3"], f"o crédito vai de 1x a {MAX_INSTALLMENTS}x", safe_max(total_cents))
    smallest = split_installments(total_cents, n)[-1]
    safe = safe_max(total_cents)
    if n == 1 or smallest >= GENERAL_MIN_INSTALLMENT_CENTS:
        return InstallmentCheck("allowed", ["3", "3.1"], "parcela atende a todas as leituras", safe)
    if n >= 7:
        return InstallmentCheck("rejected", ["3", "3.1"], "de 7x a 12x a parcela mínima é R$ 100,00", safe)
    if n >= 4:
        if smallest < MID_MIN_INSTALLMENT_CENTS:
            return InstallmentCheck("rejected", ["3", "3.1"], "de 4x a 6x a parcela mínima é R$ 80,00", safe)
        return InstallmentCheck(
            "needs_confirmation", ["3", "3.1"],
            "o §3.1 aceita parcela a partir de R$ 80,00 em 4x–6x, mas a tabela do §3 indica R$ 100,00", safe,
        )
    if total_cents < LOW_THRESHOLD_CENTS:
        return InstallmentCheck("rejected", ["3.1"], "compras abaixo de R$ 50,00 não são parceladas", safe)
    return InstallmentCheck(
        "needs_confirmation", ["3", "3.1"],
        "a regra até 3x (\"exceto abaixo de R$ 50\") admite mais de uma leitura e a tabela do §3 indica R$ 100,00",
        safe,
    )


def safe_max(total_cents: int) -> int:
    """Maior número de parcelas em que a menor parcela é de pelo menos R$ 100 (válido em todas as leituras)."""
    for n in range(MAX_INSTALLMENTS, 1, -1):
        if split_installments(total_cents, n)[-1] >= GENERAL_MIN_INSTALLMENT_CENTS:
            return n
    return 1


def can_combine_methods(total_cents: int) -> bool:
    return total_cents > COMBINATION_MIN_CENTS


@dataclass(frozen=True)
class Quote:
    product_id: int
    availability: Availability
    method: Method
    installments: int
    base_cents: int
    discount_percent: int
    offer_cents: int | None
    payment_cents: int | None
    installment_cents: list[int]
    decision: Decision
    rule_ids: list[str]
    reason: str
    safe_max_installments: int | None

    def to_dict(self) -> dict:
        return asdict(self)


def quote(
    *,
    product_id: int,
    status: str,
    stock_quantity: int,
    base_cents: int,
    promotion_percent: int,
    method: Method,
    installments: int = 1,
) -> Quote:
    avail = availability(status, stock_quantity)
    p = price(base_cents, promotion_percent)
    if avail != "available":
        # Promoção e PIX de item indisponível não autorizam oferta (§6.2, §7.3).
        return Quote(product_id, avail, method, installments, base_cents, 0, None, None, [],
                     "unavailable", ["7.3"], "produto sem venda imediata", None)
    rules = ["6.2"] if promotion_percent else []
    if method != "credit":
        if installments != 1:
            return Quote(product_id, avail, method, installments, base_cents, promotion_percent, p.offer_cents,
                         None, [], "rejected", ["3"], "só o cartão de crédito é parcelado", None)
        payment = p.pix_cents if method == "pix" else p.offer_cents
        reason = "PIX não se soma à promoção" if method == "pix" and promotion_percent else "pagamento à vista"
        return Quote(product_id, avail, method, 1, base_cents, promotion_percent, p.offer_cents, payment,
                     [payment], "allowed", ["3", *rules], reason, None)
    check = check_installments(p.offer_cents, installments)
    parts = split_installments(p.offer_cents, installments) if check.decision != "rejected" else []
    return Quote(product_id, avail, method, installments, base_cents, promotion_percent, p.offer_cents,
                 p.offer_cents if parts else None, parts, check.decision, [*check.rule_ids, *rules],
                 check.reason, check.safe_max_installments)
