# Policy retrieval evaluation

Lexical BM25 over the manual's 28 sections (manual v2.1), measured on
2026-10-31 with [`scripts/eval_retrieval.py`](../scripts/eval_retrieval.py) on
[`policy_retrieval.jsonl`](policy_retrieval.jsonl). The paraphrases were written after the synonym list and
were not used to tune it. This measures retrieval only; answer quality is reviewed on real conversations.

**Result:** base top-3: 12/12 · paraphrase top-3: 4/6 · mixed coverage: 8/9 sections.

| Case | Split | Expected | Top 3 ranked | Returned (with related) | Result |
| --- | --- | --- | --- | --- | --- |
| b01 | base | 2 | 2, 7.1, 7.3 | 2, 7.1, 7.3 | hit |
| b02 | base | 1.2 | 1.2, 9, 2 | 1.2, 9, 2, 7, 7.1 | hit |
| b03 | base | 3 | 3, 3.1, 4.1 | 3, 3.1, 4.1, 6.2, 4 | hit |
| b04 | base | 3.1 | 3.1, 3, 4.1 | 3.1, 3, 4.1, 6.2, 4 | hit |
| b05 | base | 4.1 | 4.1, 4, 3 | 4.1, 4, 3, 3.1, 6.2 | hit |
| b06 | base | 4.2 | 4.2, 8.1 | 4.2, 8.1, 8.3 | hit |
| b07 | base | 4.3 | 4.3, 4.4, 5.2 | 4.3, 4.4, 5.2, 5.3 | hit |
| b08 | base | 5.1 | 5.1, 5.2, 1.2 | 5.1, 5.2, 1.2, 5.3, 7 | hit |
| b09 | base | 5.2 | 5.2, 5.1, 8.2 | 5.2, 5.1, 8.2, 5.3, 8.1 | hit |
| b10 | base | 5.3 | 5.3, 9, 7.2 | 5.3, 9, 7.2, 5.2 | hit |
| b11 | base | 6.2 | 6.2, 6.1, 7.3 | 6.2, 6.1, 7.3, 3, 7.1 | hit |
| b12 | base | 8.1 or 8.2 | 8.3, 8.2, 8.1 | 8.3, 8.2, 8.1, 4.2 | hit |
| p01 | paraphrase | 2 | 2, 7.1, 7.3 | 2, 7.1, 7.3 | hit |
| p02 | paraphrase | 3 | 3 | 3, 3.1, 6.2 | hit |
| p03 | paraphrase | 4.1 | 6.1, 7.3, 4.3 | 6.1, 7.3, 4.3, 6.2, 7.1 | MISS |
| p04 | paraphrase | 1 or 7.1 | 1, 8.3, 7.1 | 1, 8.3, 7.1, 8.1 | hit |
| p05 | paraphrase | 7 or 1.2 |  |  | MISS |
| p06 | paraphrase | 8.3 | 8.3, 8.2, 8.1 | 8.3, 8.2, 8.1, 4.2 | hit |
| m01 | mixed | 6.2 + 3 + 3.1 | 6.2, 3.1, 3 | 6.2, 3.1, 3 | 3/3 |
| m02 | mixed | 4.2 + 8.1 | 4.2, 8.1, 4.4 | 4.2, 8.1, 4.4, 8.3, 4.3 | 2/2 |
| m03 | mixed | 4.1 + 5.2 | 4.1, 5.1, 4 | 4.1, 5.1, 4 | 1/2 |
| m04 | mixed | 5.1 + 7 | 5.1, 1.2, 5.2 | 5.1, 1.2, 5.2, 7, 5.3 | 2/2 |
