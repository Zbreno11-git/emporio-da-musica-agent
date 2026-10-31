# Findings in the source material

> Audit done on 2026-10-31 over the Artefact case, manual v2.1, the 6 CSVs and guides 01/02/03. References point to a manual section, a product or order ID, or a file, without reproducing personal data. The checking scripts ran locally on the original files.

## Reference values check

The guide-02 `oracles.json` (copied to `tests/fixtures/oracles.json`) was recomputed from the CSVs, with `Decimal` and `ROUND_HALF_UP`:

- **counts:** 9 categories, 65 products, 25 promotions, 50 customers, 20 orders and 22 items;
- **sellable products:** 61, i.e. `status = active` with stock above zero;
- **detail:** 9 products (81, 90, 94, 95, 96, 121, 127, 130, 136) and 3 orders (8, 9, 20).

**Result: 0 differences.** The relations were also checked:
- no product without a category;
- no promotion or item pointing to a missing product;
- no order without a customer and no order without items;
- every `specs` field is valid JSON;
- no product has two active promotions.

The importer now enforces all of these on every build (`tests/domain/test_import_snapshot.py`).

## Discrepancies and gaps that change the implementation

| # | Where | Finding | Proposed handling |
| --- | --- | --- | --- |
| A1 | Manual §3 × §3.1 | The §3 table sets the credit minimum installment at R$ 100. §3.1 sets R$ 80 for 4–6x. The up-to-3x rule ("except below R$ 50") has more than one reading | `quote_product` returns `needs_confirmation` when the readings diverge and offers an unambiguous option (implemented in `app/tools/quote.py`) |
| A2 | `orders.csv` × §3/§3.1 | Orders 9, 16 and 18 have installments below the §3.1 minimum (6x of R$ 58.32; 6x of R$ 71.65; 12x of R$ 38.32). Order 7 (3x of R$ 53.30) is below the §3 R$ 100 | The agent presents the historical record as it is, without "correcting" or judging it |
| A3 | Manual, cover and §1.2 × §7 | General phone (67) 3341-4444; main WhatsApp (67) 3321-4500 | Show each contact by purpose, citing the section. Hand-offs use the §7 channel |
| A4 | Manual, cover × §1.2 | The e-mail appears without an accent on the cover and with one (`empório`) in §1.2 | Prefer another documented channel; do not present the divergent e-mail as certain |
| A5 | Manual §5.1 | Metro-area shipping: R$ 35 below R$ 500, free above. **Exactly R$ 500** is not covered | Explain the bands and prepare a `policy_gap` hand-off |
| A6 | Manual §1 × `categories`/`products` | The manual mentions 300+ instruments and lists winds and orchestral strings, but categories 6, 7 and 8 have no products in the snapshot (65 products) | Answer "not in the catalog we can query", without inferring a larger catalog |
| A7 | `promotions` | Product 95 (Takamine GD20) has an **inactive** promotion. Four promotions are active, on products 90, 94, 121 and 127. The source has no validity dates | Demo case for "expired promotion" (§7.3): give the current price without promising a discount |
| A8 | `orders.total_brl` | The totals of orders 3 and 20 differ from the sum of the items' current prices | The order's historical total wins; `order_items` has no unit price |
| A9 | `orders` | Only order 8 is `shipped`. Its estimated delivery (2026-02-28) is already in the past relative to today (2026-10-31). The 8 tracking codes follow the §5.3 format | Present the date as the estimate recorded in the snapshot, without asserting the current delivery state |
| A10 | `customers` | One e-mail is shared by two customers. Empty optional fields in `orders`: `tracking_code` (12), `estimated_delivery` (12), `notes` (16) | E-mail does not identify a customer. Empty fields become `null` |
| A11 | Products 96, 130, 136 | 96 is active with stock 0; 130 is `coming_soon` with 2 units; 136 is `discontinued` with 13 units | None is shown as available; each state is stated in words |

## Discrepancies between supporting materials

| # | Where | Finding | Handling |
| --- | --- | --- | --- |
| M1 | ZIP names | `01_Guia_Visao_e_Aplicacao.zip` holds guide **03**; `03_Ressonancia_Branding.zip` holds guide **01** | Organized by content in `_private_inputs/guides/{01-branding,02-backend,03-vision}` |
| M2 | Option-1 mockup × approved decision | The mockup repeats the store avatar on each card and omits the product attribute | Follow the decision: one avatar per turn, attribute on the card (D7) |
| M3 | Guide 02 §10 | Cites `ARTEFACT_REQUIREMENTS_V1.md` and `ARTEFACT_REFERENCIAS_REPOS_SKILLS.md` | Neither file was among the received materials; guide 02 and the session prompt prevail |
| M4 | Gemini model | The initial preference was "3.1 Flash", but the account lists no such ID. Available: `gemini-3.1-flash-lite`, `gemini-3-flash-preview`, `gemini-3.5-flash`, `3.6`, `3.7` and `3.8-flash` | Choice by benchmark (D2, D14) |
| M5 | Case PDF × selection e-mail | The case asks to reply to the e-mail with the repository link; the e-mail asks for an English PDF via Google Forms, due by the end of the second business day after Sat 2026-10-31 | Do both; freeze on Tue 2026-11-03 23:59 São Paulo time (D11, D17) |
