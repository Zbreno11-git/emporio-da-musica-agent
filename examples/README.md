# Example conversations and their review

Five real conversations, captured with real Gemini on the deployed demo, revision `emporio-agent-00010-x5j` (commit `69f4b68`), on 2026-10-31 at 19:01–19:02 São Paulo time, by [`scripts/capture_examples.py`](../scripts/capture_examples.py). They are not prepared examples: each file shows what the page received, the tools called, the sources, timings and tokens, and a screenshot at 390 px. The raw responses are in [`raw/`](raw/). Customer and agent text are in Brazilian Portuguese as served, with an English translation written afterwards.

| # | Conversation | What it shows | Automatic checks | Review |
| --- | --- | --- | --- | --- |
| 01 | [Discovery with a budget, then PIX](01-discovery.md) | Only available nylon guitars at or under R$ 800; the chosen one priced on PIX | pass | PASS |
| 02 | [Promotion and PIX](02-promotion-pix.md) | R$ 359,00 −10% → R$ 323,10; PIX adds nothing (§6.2) | pass | PASS |
| 03 | [Authorized order](03-authorized-order.md) | Visitor → profile picker → profile A sees order 8 | pass | PASS |
| 04 | [Return policy with a missing fact](04-return-policy.md) | §4.1 rule, one question, then the answer with §4.1 cited from the previous turn | pass | PASS |
| 05 | [Out-of-scope item plus a bass](05-store-scope.md) | No amplifiers; available basses from the catalog | pass | PASS |

**Blockers (D13) in the five conversations: none.** No other profile's data, no divergent price, no claimed or promised action.

## How the review was done

The `qa-response` skill (a support-QA rubric: accuracy, completeness, tone, clarity, red flags) is installed with `disable-model-invocation`, so it cannot be called by the agent; I applied its checklist by hand to every agent turn. For accuracy, each claim that could change a customer's decision was traced to its source: a tool result in the raw file, a manual section, or the product's description and specs in the catalog. Verdicts: **sustained** (the source says it), **contradicted** (the source says otherwise) or **no evidence** (no source says it).

## 01 · Discovery with a budget, then PIX

| Claim | Source | Verdict |
| --- | --- | --- |
| Three nylon guitars in the budget: Yamaha C40, Tagima Memphis AC-39, Giannini GN-15 | `query_catalog` (category 5, `strings = nylon`, available); cards R$ 599,90, R$ 429,90, R$ 689,00, all ≤ R$ 800 | sustained |
| "todos com tampo em madeiras diferentes" | specs `top`: Spruce, Linden, Cedro | sustained |
| C40 "R$ 569,91 para pagamento via PIX" | `quote_product` (pix) → 56991 cents; manual §3 (5% off the list price) | sustained |
| "excelente para começar", "tampo em Spruce", "ótima projeção sonora" | C40 description: "tampo em Spruce", "Ideal para estudantes e iniciantes, com excelente projeção sonora" | sustained |

**Overall: PASS (9/10).** Notes: the model's SQL filtered the budget on the PIX price (`pix_cents`) although the customer did not mention PIX; the server re-applies the budget on the list price, so every card is within R$ 800 at the list price. The first draft of turn 1 was rejected by the server checks and rewritten (`text_corrected`). "para tu comparar" is colloquial, in line with the brand's "tu".

## 02 · Promotion and PIX

| Claim | Source | Verdict |
| --- | --- | --- |
| R$ 359,00 with 10% off, R$ 323,10 on PIX | `quote_product` (pix): base 35900, 10%, payment 32310; manual §6.2 (promotions do not stack) | sustained |
| "ukulele tenor com corpo em Sapele e tampo em Spruce" | description: "corpo em Sapele e tampo em Spruce" | sustained |
| "ótima escolha para quem prefere um instrumento um pouco maior" | description: "para quem busca um instrumento maior" | sustained |

**Overall: PASS (9/10).** Note: the answer gives the right PIX price but does not say in words that PIX adds no discount over the promotion; the card and the cited §6.2 make it visible. The model's first lookup used `name = 'Kalani KAL-700T'` (no match, ERRORS class 4) and it recovered with a `LIKE` search in the same turn.

## 03 · Authorized order

| Claim | Source | Verdict |
| --- | --- | --- |
| Turn 1: a demo profile is needed | `get_my_order` → `profile_required`; the page shows the picker | sustained |
| Turn 2: order 8 holds a Kala KA-C Concert Mogno, shipped, tracking BRJL5544332BR | `get_my_order` (profile A) | sustained |
| "A previsão registrada para a entrega era 28 de fevereiro de 2026" | order 8 `estimated_delivery` 2026-02-28, presented as the recorded estimate (source-findings A9) | sustained |
| Offer of a summary for the team because the date passed | prompt rule 8; nothing claimed as done | sustained |

**Overall: PASS (9/10).** The answer gives the data first and offers the hand-off without opening a complaint. Note: this capture uses "seu"/"você" consistently; earlier captures mixed "tu" and "você" in one answer (a tone note, not a fact).

## 04 · Return policy with a missing fact

| Claim | Source | Verdict |
| --- | --- | --- |
| Online purchases: return within 7 calendar days of receipt, original packaging, no signs of use, all accessories and manuals | manual §4.1 (`search_policy`) | sustained |
| Asks the delivery date instead of answering yes or no | prompt rule 10; the decisive fact was missing | sustained |
| Turn 2: received 10/29, "ainda está dentro do prazo de sete dias corridos" | §4.1 (carried from turn 1 and cited as "consultada na mensagem anterior"); 10/29 → 10/31 is 2 days | sustained |
| Offer to prepare a summary for the team | no hand-off claimed; `next_action` clarify | sustained |

**Overall: PASS (9/10).** The first draft of turn 2 was rejected by the server and rewritten (`text_corrected`); an earlier capture showed why that check exists: it had written "preparei este resumo" without preparing one ([`evals/model-benchmark.md`](../evals/model-benchmark.md), item 5). Note: turn 2 repeats the packaging conditions already given in turn 1; acceptable, slightly long.

## 05 · Out-of-scope item plus a bass

| Claim | Source | Verdict |
| --- | --- | --- |
| The store does not sell amplifiers, only instruments | manual §1 and §7.1 (store scope, in the prompt); no catalog category for amplifiers | sustained |
| "estes modelos disponíveis" | `query_catalog` (category 2, available): Music Man Bass 1X, Yamaha Bass 3X, Music Man Bass 4X, all `available` | sustained |

**Overall: PASS (9/10).** It answers both halves of the question in one turn and lets the cards carry the details. Data note: two of these three basses have descriptions that name another brand, and one a different string count ([source-findings A12](../docs/source-findings.md)); the answer does not repeat them.

## What this review does not cover

- Five conversations are a sample, not a measurement; the benchmark battery ([`evals/model-benchmark.md`](../evals/model-benchmark.md)) and the hosted QA run ([`docs/qa/README.md`](../docs/qa/README.md)) cover more cases with automatic checks.
- Wording that no check covers (for example "excelente para começar") was read against the descriptions here; it is not enforced by the server outside the quality word list.
