"""Topic labels for /admin come from what the agent did (tools, manual sections), never from customer text."""

from __future__ import annotations

import pytest

from app.metrics import topic_for

POLICY = [{"type": "policy", "id": "4.1", "label": "Manual da loja, seção 4.1"}]


@pytest.mark.parametrize(("tools", "sources", "handoff", "expected"), [
    ([{"name": "search_policy"}, {"name": "prepare_handoff"}], POLICY, {"reason": "policy_gap"},
     "Atendimento humano (regra sem resposta no manual)"),
    ([{"name": "get_my_order", "args": {"order_id": 8}}], [], None, "Pedido"),
    ([{"name": "query_catalog"}, {"name": "quote_product", "args": {"method": "credit"}}], [], None,
     "Parcelamento no cartão"),
    ([{"name": "quote_product", "args": {"method": "boleto"}}], [], None, "Preço e pagamento"),
    ([{"name": "search_policy"}], POLICY, None, "Regras da loja · seção 4.1"),
    ([{"name": "query_catalog"}], [], None, "Busca no catálogo"),
    ([], [], None, "Sem consulta (conversa ou fora do escopo)"),
])
def test_topic_for(tools, sources, handoff, expected):
    assert topic_for(tools, sources, handoff) == expected
