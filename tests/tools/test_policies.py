"""Manual index and section retrieval (the full labeled evaluation is scripts/eval_retrieval.py)."""

import pytest


def test_index_has_every_section_with_pages(policy_index):
    assert policy_index.manual_version == "2.1"
    assert len(policy_index.sections) == 28
    assert policy_index.by_id["6.2"]["page_start"] == 6
    assert "5%" in policy_index.by_id["3"]["text"]


def test_handoff_channel_comes_from_section_7(policy_index):
    assert policy_index.whatsapp_channel() == "(67) 3321-4500"


@pytest.mark.parametrize(("question", "section"), [
    ("Comprei online e me arrependi, posso devolver?", "4.1"),
    ("O desconto do PIX vale para produto em promoção?", "6.2"),
    ("Quanto custa o frete em Campo Grande?", "5.1"),
    ("Qual o horário de funcionamento da loja?", "2"),
])
def test_expected_section_in_top_3(policy_index, question, section):
    assert section in [sid for _, sid in policy_index.scores(question)[:3]]


def test_related_sections_are_added(policy_index):
    returned = [r["section_id"] for r in policy_index.search("O desconto do PIX vale para produto em promoção?")]
    assert "6.2" in returned and "3" in returned


def test_unrelated_question_returns_nothing(policy_index):
    assert policy_index.search("xyzzy quantum") == []
