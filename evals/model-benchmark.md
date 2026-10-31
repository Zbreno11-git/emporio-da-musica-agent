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
