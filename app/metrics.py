"""In-process aggregates for the /admin page (D20): cost, topics and most shown products since the instance started.

What is stored is decided by `record`'s signature: the trace (tool names and arguments, token usage), the cards
(public catalog ids and names) and the sources and hand-off reason. The customer's message, the agent's text and
the hand-off summary are never passed in, so they cannot be kept. Everything resets when the instance restarts.
"""

from __future__ import annotations

import threading
from collections import Counter
from datetime import datetime, timezone

HANDOFF_REASON = {"policy_gap": "regra sem resposta no manual", "policy_conflict": "regras em conflito",
                  "complaint": "reclamação", "requires_staff": "precisa da equipe"}


def turn_cost_usd(usage: dict, price: dict | None) -> float | None:
    """USD for one turn from token usage. Thinking tokens are billed as output; prices are USD per 1M tokens."""
    if not price:
        return None
    out = usage.get("output", 0) + usage.get("thoughts", 0)
    return (usage.get("input", 0) * price["input_per_mtok"] + out * price["output_per_mtok"]) / 1_000_000


def topic_for(tools: list[dict], sources: list[dict], handoff: dict | None) -> str:
    """A topic label from what the agent did, never from what the customer wrote."""
    names = [t.get("name") for t in tools]
    if handoff:
        return f"Atendimento humano ({HANDOFF_REASON.get(handoff.get('reason'), 'outro')})"
    if "get_my_order" in names:
        return "Pedido"
    quotes = [t.get("args", {}) for t in tools if t.get("name") == "quote_product"]
    if quotes:
        method = quotes[-1].get("method")
        return {"pix": "Preço no PIX", "credit": "Parcelamento no cartão"}.get(method, "Preço e pagamento")
    if "search_policy" in names:
        sections = [s["id"] for s in sources if s.get("type") == "policy"]
        return f"Regras da loja · seção {sections[0]}" if sections else "Regras da loja"
    if "query_catalog" in names:
        return "Busca no catálogo"
    return "Sem consulta (conversa ou fora do escopo)"


class TurnMetrics:
    def __init__(self, model: str, price: dict | None, price_checked_on: str | None):
        self.model, self.price, self.price_checked_on = model, price, price_checked_on
        self.started_at = datetime.now(timezone.utc)
        self._lock = threading.Lock()
        self.turns = 0
        self.cost_usd = 0.0
        self.topics: Counter[str] = Counter()
        self.products: Counter[int] = Counter()
        self.product_names: dict[int, str] = {}

    def record(self, trace: dict, cards: list[dict], sources: list[dict], handoff: dict | None) -> None:
        cost = turn_cost_usd(trace.get("usage", {}), self.price)
        topic = topic_for(trace.get("tools", []), sources, handoff)
        with self._lock:
            self.turns += 1
            self.cost_usd += cost or 0.0
            self.topics[topic] += 1
            for card in {c["product_id"]: c for c in cards}.values():  # once per turn per product
                self.products[card["product_id"]] += 1
                self.product_names[card["product_id"]] = card["name"]

    def snapshot(self) -> dict:
        with self._lock:
            priced = self.price is not None
            return {
                "since": self.started_at.isoformat(timespec="seconds"),
                "model": self.model,
                "price_checked_on": self.price_checked_on,
                "turns": self.turns,
                "cost_available": priced,
                "total_cost_usd": round(self.cost_usd, 6) if priced else None,
                "avg_cost_usd_per_answer": round(self.cost_usd / self.turns, 6) if priced and self.turns else None,
                "topics": [{"topic": t, "turns": n} for t, n in self.topics.most_common(10)],
                "top_products": [{"product_id": pid, "name": self.product_names[pid], "times_shown": n}
                                 for pid, n in self.products.most_common(3)],
            }
