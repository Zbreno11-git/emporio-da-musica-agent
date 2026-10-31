# Model benchmark (S5)

**What and how.** [`scripts/benchmark_models.py`](../scripts/benchmark_models.py) ran the same 8 scenarios (9 customer turns) twice per model on 2026-10-31, in-process against the real Gemini API, dataset `1412d32a6eeb`. The scenarios:
- Takamine → PIX;
- Kalani on PIX;
- nylon up to R$ 800;
- order 8 as profile A, and again as profile B;
- online return;
- out of scope (amplifier + bass);
- shipping of exactly R$ 500.

Blockers (D13) are checked on the delivered output. Prices come from [`pricing.json`](pricing.json) (official page, last updated 2026-10-30). Raw turns are in [`benchmark/`](benchmark/).

**Selection rule (D14, written before running):** the cheapest model that passes the 3 blockers in every run; tie → lower median latency.

| Model | Turns | Blocker turns | Quality notes | Median / p90 latency | Avg tokens in / out / thoughts | Avg cost per turn (USD) |
| --- | --- | --- | --- | --- | --- | --- |
| `gemini-3.1-flash-lite` | 18 | **0** | 2 (did not query the catalog for the bass in the out-of-scope question, both runs) | 1.85 s / 2.64 s | 6068 / 102 / 0 | **0.00167** |
| `gemini-3.5-flash-lite` | 18 | **0** | 1 (same, one run) | 1.62 s / 2.35 s | 6597 / 103 / 0 | 0.00224 |
| `gemini-3.6-flash` | 18 | **0** | 0 | 6.66 s / 9.46 s | 7606 / 115 / 764 | 0.00900 |

**Result.** All three pass every blocker. By the rule, **`gemini-3.1-flash-lite`** is pinned (`GEMINI_MODEL`, local `.env` and Cloud Run).

**Caveats.**
- `gemini-3.1-flash-lite` shuts down on 2027-05-07. The official replacement, `gemini-3.5-flash-lite`, also passed every blocker at about 1.3× the cost per turn, so it is the documented migration path.
- `gemini-3.6-flash` was the only model with no quality notes, but it was about 5× the cost and about 3.6× the median latency, mostly from thinking tokens.
- The out-of-scope miss (no bass suggested from the catalog) is a prompt issue to fix and re-check before the final capture.
- 18 turns per model is a small sample: latency figures are indicative, and cost per turn depends on the conversation length.

## Rerun after the S5.3 guards (2026-10-31, evening)

**Why.** Breno asked (2026-10-31) to avoid invented products or numbers at any cost. Reading the baseline turns and three diagnostic reruns showed four failure modes, none of them caught by the first battery:

| Failure mode (measured) | Guard added (server side, not prompt only) |
| --- | --- |
| Out of scope, baseline run 2: named "Ibanez GSR200" without any tool call. The catalog's only Ibanez bass is "Ibanez Bass 2X" | Every brand + model or model code in the text must appear in this conversation's tool results or the customer's words (`product_reference_problems`), otherwise correction, then fallback. Replayed over the 54 baseline answers: 1 hit (the GSR200), 0 false positives |
| Nylon and bass searches filtered `status = 'available'` (status holds `active`), got nothing and told the customer the store had none | `status` removed from the public schema: that query now fails loudly with "use availability". An empty discovery result also returns the sellable count per category and "this does not mean the store has none" |
| Nylon search without the nylon filter would offer a steel-string Shelby at R$ 549 | Discovery re-applies the string type the customer asked for, as it already did for the budget |
| "E no PIX?" priced by the model itself (right number, no evidence), so the server fell back to a non-answer | The correction round may call one more tool, so missing evidence is fetched instead of replaced by the fallback |
| "Posso ficar de olho e te aviso quando chegar" (a promise no system keeps) | Promises (watch stock, notify, hold an item or a price) are rejected like claimed actions |

The battery itself got stricter: an invented product (not in the catalog) is a blocker, a nylon request with a non-nylon card is a blocker, and the out-of-scope scenario expects at least one card. Raw turns, with tool arguments, are in `benchmark/*-s53.jsonl`.

| Model | Turns | Blocker turns | Quality notes | Median latency | Avg cost per turn (USD) |
| --- | --- | --- | --- | --- | --- |
| `gemini-3.1-flash-lite` | 18 | **0** | **0** | 1.90 s | **0.00185** |
| `gemini-3.5-flash-lite` | 18 | **0** | **0** | 2.00 s | 0.00241 |

**Result.** `gemini-3.1-flash-lite` stays pinned (D14). The cost per turn rose about 11% over the baseline (longer prompt, occasional correction rounds); the [cost model](cost-model.md) uses these delivered-version turns. Takamine still answers R$ 2.199,00 → R$ 2.089,05 on PIX in both runs.

**Not covered by an automatic check.** Product characteristics in free text (for example "tampo em cedro sólido", which came from the catalog description in every case read) are only governed by the prompt; the S8 `/qa-response` review checks them against the tool results.

**Check before the S7 deploy (2026-10-31).** One more run on `gemini-3.1-flash-lite` after adding "product characteristics only from the tool's description and specs" to the prompt: 9/9 turns, 0 blockers, 0 quality notes, US$ 0.00188 per turn, median 1.78 s ([`benchmark/*-s7.jsonl`](benchmark/)).
