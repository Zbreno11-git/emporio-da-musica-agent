"""Chat HTTP contracts (guide 02 §7). Input and output validated with `extra='forbid'`."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

Availability = Literal["available", "out_of_stock", "discontinued", "coming_soon"]
NextAction = Literal["none", "choose_profile", "clarify", "contact_store"]
HandoffReason = Literal["policy_gap", "policy_conflict", "complaint", "requires_staff"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChatRequest(Strict):
    request_id: UUID
    message: str = Field(min_length=1, max_length=2000)


class ProfileRequest(Strict):
    profile: str = Field(min_length=1, max_length=32)


class Card(Strict):
    product_id: int
    name: str
    attribute: str
    availability: Availability
    base_cents: int
    offer_cents: int
    discount_percent: int
    payment_cents: int | None = None
    payment_method: Literal["table", "pix", "debit", "credit", "boleto"] | None = None
    installments: int | None = None
    installment_cents: int | None = None


class Source(Strict):
    type: Literal["catalog", "policy", "order"]
    id: str
    label: str
    page_start: int | None = None
    page_end: int | None = None


class Handoff(Strict):
    reason: HandoffReason
    summary: str = Field(max_length=400)
    channel_label: str
    destination: str
    delivery_status: Literal["prepared"]


class ChatResponse(Strict):
    request_id: UUID
    text: str
    cards: list[Card]
    sources: list[Source]
    next_action: NextAction
    handoff: Handoff | None = None
    trace: dict | None = None  # optional technical inspection (tools, timings, model); no personal data


class ErrorBody(Strict):
    code: str
    message: str
    retryable: bool
    request_id: UUID | None = None
