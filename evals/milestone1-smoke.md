# Milestone 1 smoke test (real Gemini)

**What it checks.** In one session, "Quanto custa o Takamine GD20?" must return a card for product 95 at 219900 cents, and the follow-up "e no PIX?" must return 208905 cents on PIX for the same product. The answer runs through the real HTTP app in-process ([`scripts/smoke_gemini.py`](../scripts/smoke_gemini.py)).

**When and with what.** 2026-10-31, `google-genai` 2.34.0, dataset `1412d32a6eeb`, one run per model. The raw outputs are in [`smoke/`](smoke/).

| Model | Turn | Result | Wall time | Tools called | Tokens in / out / thoughts |
| --- | --- | --- | --- | --- | --- |
| `gemini-3.5-flash` | Takamine price | ✅ 219900 | 9.62 s | query_catalog, quote_product | 6117 / 120 / 1044 |
| `gemini-3.5-flash` | "e no PIX?" | ✅ 208905 | 3.85 s | quote_product | 6393 / 58 / 329 |
| `gemini-3.1-flash-lite` | Takamine price | ✅ 219900 | 1.76 s | query_catalog | 3357 / 105 / 0 |
| `gemini-3.1-flash-lite` | "e no PIX?" | ✅ 208905 | 1.49 s | quote_product | 3946 / 62 / 0 |

**Reading.** Both candidates pass milestone 1 with no text correction or fallback. `3.1-flash-lite` answered the PIX price already in the first turn, using `pix_cents` from the catalog result, which is valid evidence. One run per model is not a latency measurement; the S5 benchmark repeats a wider battery and applies the D14 selection rule.
