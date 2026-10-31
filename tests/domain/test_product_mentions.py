"""Product references in the model's text must come from evidence (tool results or the customer's own words).

Breno's rule (2026-10-31): no invented products or numbers, at any cost. Prices are already checked; this file
covers product and model names. The real case: the benchmark's out-of-scope run named "Ibanez GSR200", a model
the catalog does not have, without calling any tool.
"""

from __future__ import annotations

import sqlite3

from app.agent import BRANDS, product_reference_problems

EVIDENCE = ("Takamine GD20 Dreadnought Natural\nIbanez Bass 2X Electric Bass\nYamaha C40 Nylon Natural\n"
            "Bateria Acústica Yamaha Kit 1 Studio\nMusic Man Bass 1X Electric Bass\nBRJL5544332BR")


def test_invented_model_is_flagged():
    problems = product_reference_problems("Mas posso te indicar o Ibanez GSR200, ótimo para começar.", EVIDENCE)
    assert problems and "Ibanez GSR200" in problems[0]


def test_model_code_without_brand_is_flagged():
    assert product_reference_problems("O GSR200 tem um braço confortável.", EVIDENCE)


def test_brand_and_model_absent_from_evidence_are_flagged():
    assert product_reference_problems("Uma Fender Stratocaster seria ideal.", EVIDENCE)
    assert product_reference_problems("A Yamaha Pacifica é leve.", EVIDENCE)  # real brand, invented model


def test_references_backed_by_evidence_pass():
    for text in ["O Takamine GD20 está por R$ 2.199,00.",
                 "Temos o Ibanez Bass 2X disponível.",
                 "A bateria Yamaha Kit 1 é uma boa opção.",
                 "O Music Man Bass 1X tem graves fortes.",
                 "O C40 é ótimo para começar.",
                 "O código de rastreio é BRJL5544332BR."]:
        assert product_reference_problems(text, EVIDENCE) == [], text


def test_bare_brands_and_ordinary_text_pass():
    for text in ["Trabalhamos com Takamine, Yamaha e Ibanez.",
                 "Não encontrei Fender no catálogo agora.",
                 "Dá para parcelar em até 12X no cartão, conforme a seção 3.1.",
                 "A gente não vende amplificadores. Quer que eu procure um baixo?"]:
        assert product_reference_problems(text, EVIDENCE) == [], text


def test_catalog_brands_are_all_in_the_lexicon(snapshot_build):
    """Both ends compared: a new brand in the catalog without a lexicon entry would go unchecked."""
    con = sqlite3.connect(f"file:{snapshot_build / 'catalog.db'}?mode=ro", uri=True)
    names = [r[0] for r in con.execute("SELECT name FROM products")]
    con.close()
    missing = [n for n in names if not any(f" {b} " in f" {n} " for b in BRANDS)]
    assert missing == []


# --- sound and build qualities (D22): they must come from the product data of this conversation -------------------

from app.agent import quality_problems  # noqa: E402

C40 = "Violão clássico com tampo em Spruce e fundo/laterais em Meranti. Ideal para estudantes e iniciantes, com excelente projeção sonora."
TAKAMINE = "Violão dreadnought Takamine com tampo sólido em cedro. Excelente para fingerstyle com timbre quente e definido."


def test_quality_not_in_the_description_is_flagged():
    """Real case (capture 2026-10-31): the C40 was said to have "um timbre bem definido"; its description has no timbre."""
    problems = quality_problems("Ele tem um timbre bem definido e é muito resistente.", C40)
    assert any("timbre" in p for p in problems) and any("resistent" in p for p in problems)


def test_quality_backed_by_the_description_passes_with_accents_folded():
    assert quality_problems("Tem uma ótima projeção sonora.", C40) == []
    assert quality_problems("O timbre é quente, ótimo para fingerstyle.", TAKAMINE) == []
    assert quality_problems("Projecao boa.", C40) == []


def test_ordinary_words_are_not_quality_claims():
    assert quality_problems("Quer que eu prepare um resumo? O prazo é de sete dias corridos.", C40) == []
