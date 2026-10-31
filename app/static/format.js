// Pure display rules for the chat (no DOM): what a card, a source list and a technical line show.
// Every value comes from the API response; nothing here computes a price, it only formats cents.

const BRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export const AVAILABILITY = {
  available: "Disponível",
  out_of_stock: "Temporariamente esgotado",
  discontinued: "Fora de linha",
  coming_soon: "Em breve",
};

const METHOD = { pix: "no PIX", debit: "no débito", boleto: "no boleto", credit: "no cartão", table: "" };

export function formatCents(cents) {
  return BRL.format(cents / 100);
}

export function priceView(card) {
  const available = card.availability === "available";
  const view = {
    available,
    availability: AVAILABILITY[card.availability] ?? "Consultar disponibilidade",
    current: formatCents(card.offer_cents),
    list: null,
    percent: null,
    payment: null,
  };
  if (!available) return view; // the backend already drops promotions for items that cannot be bought
  if (card.discount_percent > 0) {
    view.list = formatCents(card.base_cents);
    view.percent = `-${card.discount_percent}%`;
  }
  // "table" is the catalog price itself: no payment line, so no condition ("à vista") the store never stated.
  if (card.payment_cents != null && card.payment_method && card.payment_method !== "table") {
    let label = METHOD[card.payment_method] ?? "";
    if (card.payment_method === "credit" && card.installments > 1 && card.installment_cents != null) {
      label = `em ${card.installments}x de ${formatCents(card.installment_cents)} no cartão`;
    }
    view.payment = { amount: formatCents(card.payment_cents), label };
  }
  return view;
}

export function sourcesView(sources) {
  const seen = new Set();
  const out = [];
  for (const s of sources ?? []) {
    let label = s.label;
    if (s.type === "policy" && s.page_start) {
      label += s.page_end && s.page_end !== s.page_start ? ` (p. ${s.page_start}–${s.page_end})` : ` (p. ${s.page_start})`;
    }
    if (!seen.has(label)) {
      seen.add(label);
      out.push(label);
    }
  }
  return out;
}

export function traceLines(trace) {
  if (!trace) return [];
  const tools = (trace.tools ?? []).map((t) => t.name).join(", ") || "nenhuma";
  const usage = trace.usage ?? {};
  const lines = [
    `Modelo: ${trace.model}`,
    `Tempo: ${(trace.duration_ms / 1000).toFixed(1)} s · chamadas ao modelo: ${trace.model_calls}`,
    `Ferramentas: ${tools}`,
    `Tokens: ${usage.input ?? 0} de entrada, ${(usage.output ?? 0) + (usage.thoughts ?? 0)} de saída`,
  ];
  if (trace.text_fallback) lines.push("O texto do modelo não passou na conferência; a resposta foi montada pelo servidor.");
  else if (trace.text_corrected) lines.push("O servidor pediu uma correção ao modelo antes de mostrar a resposta.");
  return lines;
}
