# 02 · Promotion and PIX do not stack

> Real conversation captured on the deployed demo (not a prepared example). Customer and agent text are in Brazilian Portuguese, as served; the English translation was written afterwards for the evaluators.

| | |
| --- | --- |
| URL | https://emporio-agent-669786539213.southamerica-east1.run.app |
| Revision / commit | `emporio-agent-00011-z2g` / `ec6f6d6` |
| Model | `gemini-3.1-flash-lite` |
| Dataset | `1412d32a6eeb` |
| Captured | 2026-10-31 20:16 (São Paulo) |
| Screenshot | [02-promotion-pix-390.png](screens/02-promotion-pix-390.png) |

## Conversation

**Turn 1 · Customer:** Quanto fica o Kalani KAL-700T no PIX?
<br>*EN:* How much is the Kalani KAL-700T with PIX?

**Turn 1 · Empório:** O Kalani KAL-700T Tenor Natural está com um desconto de 10%, saindo de R$ 359,00 por R$ 323,10. Como temos uma promoção ativa, esse é o valor final para o pagamento via PIX.
<br>*EN:* The Kalani KAL-700T Tenor Natural has a 10% discount, from R$ 359,00 down to R$ 323,10. Since there is an active promotion, that is the final price for PIX payment.

Cards shown:
- `#127` Kalani KAL-700T Tenor Natural · Ukulele tenor · R$ 359,00 −10% → R$ 323,10; pix: R$ 323,10 · available

<sub>Tools: `query_catalog` (intent=lookup), `quote_product` (product_id=127, method=pix) · sources: Catálogo da loja; Manual da loja, seção 3; Manual da loja, seção 6.2 · next_action `none` · 3.07 s in the browser (2766 ms server) · 3 model calls · tokens in/out 9893/128</sub>

## Automatic checks

| Check | Result |
| --- | --- |
| turn 1: no claimed or promised action | pass |
| turn 1: not rewritten by the server fallback | pass |
| card: product 127, list 35900, 10%, PIX 32310 | pass |
| text states R$ 359,00, 10% and R$ 323,10 together; never R$ 306,95 | pass |

## Review

See [the review of all five conversations](README.md).
