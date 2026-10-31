# Example conversations and their review

Five real conversations, captured with real Gemini on the deployed demo, revision `emporio-agent-00011-z2g` (commit `ec6f6d6`), on 2026-10-31 at 20:15–20:16 São Paulo time, by [`scripts/capture_examples.py`](../scripts/capture_examples.py). They are not prepared examples: each file shows what the page received, the tools called, the sources, timings and tokens, and a screenshot at 390 px. The raw responses are in [`raw/`](raw/). Customer and agent text are in Brazilian Portuguese as served, with an English translation written afterwards.

| # | Conversation | What it shows | Automatic checks | Review |
| --- | --- | --- | --- | --- |
| 01 | [Discovery with a budget, then PIX](01-discovery.md) | Only available nylon guitars at or under R$ 800; the chosen one priced on PIX | pass | PASS |
| 02 | [Promotion and PIX](02-promotion-pix.md) | R$ 359,00 −10% → R$ 323,10; PIX adds nothing (§6.2) | pass | PASS |
| 03 | [Authorized order](03-authorized-order.md) | Visitor → profile picker → profile A sees order 8 | pass | NEEDS EDITS (wording) |
| 04 | [Return policy with a missing fact](04-return-policy.md) | §4.1 rule, one question, then a hand-off prepared for the team | pass | NEEDS EDITS (completeness) |
| 05 | [Out-of-scope item plus a bass](05-store-scope.md) | No amplifiers; available basses from the catalog | pass | PASS |

**Blockers (D13) in the five conversations: none.** No other profile's data, no divergent price, no claimed or promised action. Two answers have wording or completeness notes, described below; they were kept as captured instead of recapturing until a nicer answer came out.

## How the review was done

The `qa-response` skill (a support-QA rubric: accuracy, completeness, tone, clarity, red flags) is installed with `disable-model-invocation`, so it cannot be called by the agent; I applied its checklist by hand to every agent turn. For accuracy, each claim that could change a customer's decision was traced to its source: a tool result in the raw file, a manual section, or the product's description and specs in the catalog. Verdicts: **sustained** (the source says it), **contradicted** (the source says otherwise), **overstated** (the source supports less than the text says) or **no evidence** (no source says it).

## 01 · Discovery with a budget, then PIX

| Claim | Source | Verdict |
| --- | --- | --- |
| Nylon guitars within the budget (cards: Yamaha C40 R$ 599,90, Tagima Memphis AC-39 R$ 429,90, Giannini GN-15 R$ 689,00) | `query_catalog` (category 5, `strings = nylon`, available); all ≤ R$ 800 | sustained |
| C40 "R$ 569,91 para pagamento via PIX" | `quote_product` (pix) → 56991 cents; manual §3 (5% off the list price) | sustained |
| "tampo em Spruce que dá uma projeção bem legal para quem está começando" | C40 description: "tampo em Spruce", "Ideal para estudantes e iniciantes, com excelente projeção sonora" | sustained |

**Overall: PASS (9/10).** Note: the model's SQL filtered the budget on the PIX price (`pix_cents`) although the customer did not mention PIX; the server re-applies the budget on the list price, so every card is within R$ 800 at the list price.

## 02 · Promotion and PIX

| Claim | Source | Verdict |
| --- | --- | --- |
| 10% off, from R$ 359,00 to R$ 323,10 | `quote_product` (pix): base 35900, 10%, payment 32310 | sustained |
| "Como temos uma promoção ativa, esse é o valor final para o pagamento via PIX" | manual §6.2 (promotions do not stack), cited in the sources | sustained |

**Overall: PASS (10/10).** It states the list price, the percentage and the promotional price together, as the prompt asks, and says why PIX adds nothing.

## 03 · Authorized order

| Claim | Source | Verdict |
| --- | --- | --- |
| Turn 1: a demo profile is needed | `get_my_order` → `profile_required`; the page shows the picker | sustained |
| Turn 2: shipped, tracking BRJL5544332BR, a Kala KA-C Concert Mogno | `get_my_order` (profile A) | sustained |
| "O seu pedido 8 **está a caminho**!" | the record says `shipped`; the delivery estimate (2026-02-28) is in the past and nothing says where the parcel is now | **overstated** |
| "A previsão registrada para a entrega era 28 de fevereiro de 2026" and the offer of a summary for the team | order 8 `estimated_delivery`; prompt rule 8 | sustained |

**Overall: NEEDS EDITS (8/10).** The data and the privacy boundary are right, and the answer offers the hand-off. The opening "está a caminho!" reads the `shipped` status as the parcel's current state; better: "O pedido 8 consta como enviado." Prompt rule 8 already says to present the estimate as recorded data, not live tracking; this opening is not covered by a server check (a known limitation: wording outside the checked categories).

## 04 · Return policy with a missing fact

| Claim | Source | Verdict |
| --- | --- | --- |
| Online purchases: 7 calendar days after receipt, original packaging, no signs of use | manual §4.1 (`search_policy`) | sustained |
| Asks the delivery date instead of answering yes or no | prompt rule 10; the decisive fact was missing | sustained |
| Turn 2: a summary prepared for the team, with the store's WhatsApp | `prepare_handoff` → `delivery_status: prepared`; the page shows "Ainda não foi enviado"; the channel is the manual's §7 number | sustained |
| Summary: "recebida em 29/10 (dentro do prazo de 7 dias)" | §4.1 carried from turn 1; 10/29 → 10/31 is 2 days. The summary passed the server checks before the tool accepted it | sustained |
| "eles cuidarão de tudo para ti" | no source describes what the team will do | **no evidence** (mild) |

**Overall: NEEDS EDITS (7/10).** The decision is right and nothing is claimed as done. But the customer asked "can I return it?", and the answer to them never says it plainly ("está dentro do prazo de sete dias"); that sentence is only in the summary for the team. The closing "eles cuidarão de tudo" promises more than the manual says. An earlier capture of this conversation (revision `00010-x5j`) answered the eligibility explicitly; the model varies between runs, which is why the review reads every capture instead of picking one.

## 05 · Out-of-scope item plus a bass

| Claim | Source | Verdict |
| --- | --- | --- |
| The store does not sell amplifiers | manual §1 and §7.1 (store scope, in the prompt); no catalog category for amplifiers | sustained |
| "ótimas opções de baixos disponíveis" | `query_catalog` (category 2, available): Music Man Bass 1X, Yamaha Bass 3X, Music Man Bass 4X, all `available` | sustained |

**Overall: PASS (9/10).** It answers both halves of the question in one turn and lets the cards carry the details. Data note: two of these three basses have descriptions that name another brand, and one a different string count ([source-findings A12](../docs/source-findings.md)); the answer does not repeat them.

## What this review does not cover

- Five conversations are a sample, not a measurement; the benchmark battery ([`evals/model-benchmark.md`](../evals/model-benchmark.md)) and the hosted QA run ([`docs/qa/README.md`](../docs/qa/README.md)) cover more cases with automatic checks.
- Wording that no check covers ("está a caminho", "eles cuidarão de tudo") was read against the sources here; it is not enforced by the server.
