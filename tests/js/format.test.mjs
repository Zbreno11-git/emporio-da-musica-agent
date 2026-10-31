// Display rules of the chat page (app/static/format.js). Run: node --test tests/js
import assert from "node:assert/strict";
import test from "node:test";

import { formatCents, priceView, sourcesView, traceLines } from "../../app/static/format.js";

const NBSP = "\u00a0"; // Intl puts a no-break space after "R$"

test("cents are formatted as BRL without float drift", () => {
  assert.equal(formatCents(219900), `R$${NBSP}2.199,00`);
  assert.equal(formatCents(208905), `R$${NBSP}2.089,05`);
  assert.equal(formatCents(29), `R$${NBSP}0,29`);
});

test("promotion shows list price, percentage and current price together", () => {
  const v = priceView({ availability: "available", base_cents: 35900, offer_cents: 32310, discount_percent: 10,
                        payment_cents: 32310, payment_method: "pix" });
  assert.equal(v.list, `R$${NBSP}359,00`);
  assert.equal(v.percent, "-10%");
  assert.equal(v.current, `R$${NBSP}323,10`);
  assert.deepEqual(v.payment, { amount: `R$${NBSP}323,10`, label: "no PIX" });
});

test("no promotion: no struck list price", () => {
  const v = priceView({ availability: "available", base_cents: 219900, offer_cents: 219900, discount_percent: 0 });
  assert.equal(v.list, null);
  assert.equal(v.current, `R$${NBSP}2.199,00`);
  assert.equal(v.payment, null);
});

test("installments are shown with the per-installment value", () => {
  const v = priceView({ availability: "available", base_cents: 219900, offer_cents: 219900, discount_percent: 0,
                        payment_cents: 219900, payment_method: "credit", installments: 10, installment_cents: 21990 });
  assert.equal(v.payment.label, `em 10x de R$${NBSP}219,90 no cartão`);
});

test("unavailable products say so in words and get no offer", () => {
  const v = priceView({ availability: "discontinued", base_cents: 100000, offer_cents: 100000, discount_percent: 15,
                        payment_cents: 95000, payment_method: "pix" });
  assert.equal(v.available, false);
  assert.equal(v.availability, "Fora de linha");
  assert.equal(v.list, null);
  assert.equal(v.payment, null);
});

test("sources are de-duplicated and policy pages shown", () => {
  const labels = sourcesView([
    { type: "catalog", id: "product:81", label: "Catálogo da loja" },
    { type: "catalog", id: "product:83", label: "Catálogo da loja" },
    { type: "policy", id: "6.2", label: "Manual da loja, seção 6.2", page_start: 4, page_end: 4 },
    { type: "policy", id: "3.1", label: "Manual da loja, seção 3.1", page_start: 2, page_end: 3 },
  ]);
  assert.deepEqual(labels, ["Catálogo da loja", "Manual da loja, seção 6.2 (p. 4)", "Manual da loja, seção 3.1 (p. 2–3)"]);
});

test("technical lines say when the server rewrote the answer", () => {
  const lines = traceLines({ model: "m", duration_ms: 1840, model_calls: 2, tools: [{ name: "query_catalog" }],
                             usage: { input: 5000, output: 80, thoughts: 20 }, text_fallback: true });
  assert.ok(lines.includes("Tokens: 5000 de entrada, 100 de saída"));
  assert.ok(lines.at(-1).startsWith("O texto do modelo não passou"));
});

test("a table-price quote adds no payment condition", () => {
  const v = priceView({ availability: "available", base_cents: 219900, offer_cents: 219900, discount_percent: 0,
                        payment_cents: 219900, payment_method: "table" });
  assert.equal(v.payment, null);
  assert.equal(v.current, `R$${NBSP}2.199,00`);
});
