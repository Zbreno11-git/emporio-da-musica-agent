"""Policy retrieval over the manual's sections (lexical BM25 with related-section expansion).

The index is built offline by scripts/build_policy_index.py. Search returns up to 3 sections by score plus up to
2 sections linked to them (e.g. §3 PIX ↔ §6.2 promotions), each with its id, title, pages and text, so the agent
can cite exactly what it used. Portuguese text is folded (lowercase, no accents), stopwords removed and words
lightly stemmed, which is enough for a 28-section manual.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

STOPWORDS = set("""a o as os um uma uns umas de do da dos das em no na nos nas por pelo pela pelos pelas para pra
com sem e ou que se ao aos à às é ser foi são era meu minha meus minhas teu tua seu sua seus suas eu tu você voce
vocês ele ela eles elas me te nos lhe isso isto esse essa este esta aquele aquela qual quais como quando onde quanto
quanta quantos quantas tem ter há já mais menos muito pouco bem posso pode podem consigo quero queria gostaria sobre
até ate não nao sim lá aqui ainda também tambem então entao mas porque pois oi olá ola obrigado obrigada""".split())

# A few customer words mapped to the manual's vocabulary.
SYNONYMS = {
    "devolver": "devolucao", "devolvo": "devolucao", "arrependi": "arrependimento", "arrependimento": "arrependimento",
    "trocar": "troca", "troco": "troca", "parcelar": "parcelamento", "parcelas": "parcelamento", "parcela": "parcelamento",
    "vezes": "parcelamento", "cartao": "cartao", "entrega": "entrega", "entregam": "entrega", "frete": "frete",
    "abre": "horario", "abrem": "horario", "aberto": "horario", "fecha": "horario", "funcionamento": "horario",
    "horas": "horario", "endereco": "endereco", "fica": "endereco", "localizacao": "endereco", "defeito": "defeito",
    "quebrou": "defeito", "estragou": "defeito", "garantia": "garantia", "promocao": "promocao", "desconto": "desconto",
    "rastrear": "rastreamento", "rastreio": "rastreamento", "codigo": "rastreamento", "reclamar": "reclamacao",
    "reclamacao": "reclamacao", "dados": "dados", "lgpd": "dados", "whatsapp": "whatsapp", "telefone": "telefone",
    "amplificador": "acessorios", "cabo": "acessorios", "corda": "acessorios", "cordas": "acessorios",
    "palheta": "acessorios", "pedal": "acessorios", "case": "acessorios", "acessorio": "acessorios",
}


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def stem(word: str) -> str:
    for suffix in ("coes", "soes", "mente", "ades", "idade", "cao", "sao", "oes", "ais", "eis", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def tokens(text: str) -> list[str]:
    out = []
    for word in re.findall(r"[a-z0-9]+", fold(text)):
        if word in STOPWORDS or len(word) < 2:
            continue
        out.append(stem(SYNONYMS.get(word, word)))
    return out


@dataclass
class PolicyIndex:
    manual_version: str
    source_hash: str
    sections: list[dict]

    @classmethod
    def load(cls, path: Path) -> "PolicyIndex":
        data = json.loads(path.read_text())
        return cls(data["manual_version"], data["source_hash"], data["sections"])

    def __post_init__(self):
        self.by_id = {s["id"]: s for s in self.sections}
        # Title tokens count twice; heading-only sections (5, 6, 8) are searchable by title.
        self.docs = [tokens(s["title"]) * 2 + tokens(s["text"]) for s in self.sections]
        self.avg_len = sum(map(len, self.docs)) / len(self.docs)
        df = Counter(t for doc in self.docs for t in set(doc))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.tf = [Counter(doc) for doc in self.docs]

    def scores(self, question: str, k1: float = 1.4, b: float = 0.75) -> list[tuple[float, str]]:
        q = tokens(question)
        out = []
        for i, s in enumerate(self.sections):
            tf, dl = self.tf[i], len(self.docs[i])
            score = sum(self.idf.get(t, 0) * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / self.avg_len))
                        for t in q if t in tf)
            if score > 0 and s["text"]:
                out.append((score, s["id"]))
        return sorted(out, key=lambda x: (-x[0], x[1]))

    def search(self, question: str, top_k: int = 3, max_related: int = 2) -> list[dict]:
        ranked = [sid for _, sid in self.scores(question)[:top_k]]
        related: list[str] = []
        for sid in ranked:
            for rid in self.by_id[sid]["related_ids"]:
                if rid not in ranked and rid not in related and self.by_id[rid]["text"]:
                    related.append(rid)
        return [self.section(sid, related=sid not in ranked) for sid in ranked + related[:max_related]]

    def section(self, sid: str, related: bool = False) -> dict:
        s = self.by_id[sid]
        return {"section_id": sid, "title": s["title"], "page_start": s["page_start"], "page_end": s["page_end"],
                "text": s["text"], "related": related}

    def whatsapp_channel(self) -> str:
        """The hand-off destination comes from the manual (§7), never from code constants."""
        m = re.search(r"WhatsApp\s+(\(\d{2}\)\s*\d{4,5}-\d{4})", self.by_id["7"]["text"])
        if not m:
            raise ValueError("manual §7 does not state a WhatsApp number; rebuild or review the index")
        return m.group(1)
