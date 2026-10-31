"""Price, promotion, PIX and installments in integer cents.

Store manual (v2.1) rules:
- §3: PIX gets 5% off the list price; credit card up to 12 interest-free installments, minimum R$ 100 each.
- §3.1: up to 3x with no minimum "except below R$ 50"; 4–6x minimum R$ 80; 7–12x minimum R$ 100;
  combining payment methods only above R$ 2,000.
- §6.2: promotions do not stack; the PIX discount does not apply on top of a promotional price.

Where §3 and §3.1 lead to different outcomes, the decision is `needs_confirmation` and the function
offers an option that is valid under every reading. Rounding is ROUND_HALF_UP, once, on the final value.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

PIX_DISCOUNT_PERCENT = 5
MAX_INSTALLMENTS = 12
GENERAL_MIN_INSTALLMENT_CENTS = 10_000  # §3 and §3.1 (7–12x)
MID_MIN_INSTALLMENT_CENTS = 8_000  # §3.1 (4–6x)
LOW_THRESHOLD_CENTS = 5_000  # §3.1 (up to 3x, "except below R$ 50")
COMBINATION_MIN_CENTS = 200_000  # §3.1, "above R$ 2,000"

Method = Literal["table", "pix", "debit", "credit", "boleto"]
Availability = Literal["available", "out_of_stock", "discontinued", "coming_soon"]
Decision = Literal["allowed", "rejected", "needs_confirmation", "unavailable"]


def to_cents(value: str | Decimal) -> int:
    """Convert a textual BRL amount ("599.9") to cents without going through float."""
    amount = Decimal(value) if isinstance(value, Decimal) else Decimal(str(value).strip())
    if amount < 0:
        raise ValueError(f"negative amount: {value!r}")
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
    raise ValueError(f"unknown status: {status!r}")


@dataclass(frozen=True)
class Pricing:
    base_cents: int
    promotion_percent: int
    offer_cents: int
    pix_cents: int


def price(base_cents: int, promotion_percent: int = 0) -> Pricing:
    """Current price and PIX price. With an active promotion, PIX = offer (§6.2); otherwise 5% off list (§3)."""
    if not 0 <= promotion_percent < 100:
        raise ValueError(f"promotion percent out of range: {promotion_percent}")
    offer = _percent_of(base_cents, 100 - promotion_percent) if promotion_percent else base_cents
    pix = offer if promotion_percent else _percent_of(base_cents, 100 - PIX_DISCOUNT_PERCENT)
    return Pricing(base_cents, promotion_percent, offer, pix)


def split_installments(total_cents: int, n: int) -> list[int]:
    """Split the total into n installments that add up exactly (the first ones carry the remainder)."""
    q, r = divmod(total_cents, n)
    return [q + 1] * r + [q] * (n - r)


@dataclass(frozen=True)
class InstallmentCheck:
    decision: Decision
    rule_ids: list[str]
    reason: str
    safe_max_installments: int  # largest n valid under every reading (1 = single payment)


def check_installments(total_cents: int, n: int) -> InstallmentCheck:
    if not 1 <= n <= MAX_INSTALLMENTS:
        return InstallmentCheck("rejected", ["3"], f"credit goes from 1x to {MAX_INSTALLMENTS}x", safe_max(total_cents))
    smallest = split_installments(total_cents, n)[-1]
    safe = safe_max(total_cents)
    if n == 1 or smallest >= GENERAL_MIN_INSTALLMENT_CENTS:
        return InstallmentCheck("allowed", ["3", "3.1"], "installment meets every reading", safe)
    if n >= 7:
        return InstallmentCheck("rejected", ["3", "3.1"], "from 7x to 12x the minimum installment is R$ 100.00", safe)
    if n >= 4:
        if smallest < MID_MIN_INSTALLMENT_CENTS:
            return InstallmentCheck("rejected", ["3", "3.1"], "from 4x to 6x the minimum installment is R$ 80.00", safe)
        return InstallmentCheck(
            "needs_confirmation", ["3", "3.1"],
            "§3.1 accepts installments from R$ 80.00 in 4x–6x, but the §3 table states R$ 100.00", safe,
        )
    if total_cents < LOW_THRESHOLD_CENTS:
        return InstallmentCheck("rejected", ["3.1"], "purchases below R$ 50.00 are not split", safe)
    return InstallmentCheck(
        "needs_confirmation", ["3", "3.1"],
        "the up-to-3x rule (\"except below R$ 50\") has more than one reading and the §3 table states R$ 100.00",
        safe,
    )


def safe_max(total_cents: int) -> int:
    """Largest installment count whose smallest installment is at least R$ 100 (valid under every reading)."""
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
        # Promotion and PIX prices of an unavailable item do not authorize an offer (§6.2, §7.3).
        return Quote(product_id, avail, method, installments, base_cents, 0, None, None, [],
                     "unavailable", ["7.3"], "product not available for immediate sale", None)
    rules = ["6.2"] if promotion_percent else []
    if method != "credit":
        if installments != 1:
            return Quote(product_id, avail, method, installments, base_cents, promotion_percent, p.offer_cents,
                         None, [], "rejected", ["3"], "only credit card payments can be split", None)
        payment = p.pix_cents if method == "pix" else p.offer_cents
        reason = "PIX does not stack with the promotion" if method == "pix" and promotion_percent else "single payment"
        return Quote(product_id, avail, method, 1, base_cents, promotion_percent, p.offer_cents, payment,
                     [payment], "allowed", ["3", *rules], reason, None)
    check = check_installments(p.offer_cents, installments)
    parts = split_installments(p.offer_cents, installments) if check.decision != "rejected" else []
    return Quote(product_id, avail, method, installments, base_cents, promotion_percent, p.offer_cents,
                 p.offer_cents if parts else None, parts, check.decision, [*check.rule_ids, *rules],
                 check.reason, check.safe_max_installments)
