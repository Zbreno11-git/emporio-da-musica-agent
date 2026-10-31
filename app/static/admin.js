// /admin: the token stays in this module's memory only; the numbers come from /admin/api/stats (D20).
const $ = (selector) => document.querySelector(selector);
let token = "";

const USD = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD", minimumFractionDigits: 5, maximumFractionDigits: 5 });
const USD2 = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD", minimumFractionDigits: 2, maximumFractionDigits: 4 });
const WHEN = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short", timeZone: "America/Campo_Grande" });

function row(...cells) {
  const tr = document.createElement("tr");
  cells.forEach((text, i) => {
    const td = document.createElement("td");
    td.textContent = text;
    if (i > 0) td.className = "num";
    tr.append(td);
  });
  return tr;
}

function render(s) {
  $("#since").textContent = `Números desde que esta instância do servidor começou (${WHEN.format(new Date(s.since))}, horário de Campo Grande). Reiniciar o servidor zera tudo. Modelo: ${s.model}.`;
  $("#turns").textContent = String(s.turns);
  if (s.cost_available) {
    $("#avg").textContent = s.avg_cost_usd_per_answer == null ? "sem respostas ainda" : USD.format(s.avg_cost_usd_per_answer);
    $("#total").textContent = USD2.format(s.total_cost_usd);
    $("#cost-note").textContent = `Custo estimado = tokens de cada resposta × preço oficial do modelo conferido em ${s.price_checked_on}. Não inclui o servidor (Cloud Run).`;
  } else {
    $("#avg").textContent = "indisponível";
    $("#total").textContent = "indisponível";
    $("#cost-note").textContent = "O preço deste modelo não está no arquivo de preços, então o custo não é calculado.";
  }
  const topics = $("#topics tbody");
  topics.replaceChildren(...(s.topics.length ? s.topics.map((t) => row(t.topic, String(t.turns))) : [row("Nenhuma resposta ainda", "")]));
  const products = $("#products");
  products.replaceChildren(...s.top_products.map((p) => {
    const li = document.createElement("li");
    li.textContent = `${p.name} — ${p.times_shown} ${p.times_shown === 1 ? "vez" : "vezes"}`;
    return li;
  }));
  if (!s.top_products.length) {
    const li = document.createElement("li");
    li.textContent = "Nenhum produto mostrado ainda";
    products.append(li);
  }
  $("#stats").hidden = false;
}

async function load() {
  const res = await fetch("/admin/api/stats", { headers: { "X-Admin-Token": token }, cache: "no-store" });
  if (!res.ok) {
    token = "";
    $("#stats").hidden = true;
    $("#unlock").hidden = false;
    $("#unlock-error").textContent = "Token inválido, ou o painel está desativado neste servidor.";
    return;
  }
  $("#unlock").hidden = true;
  render(await res.json());
}

$("#unlock").addEventListener("submit", (event) => {
  event.preventDefault();
  token = $("#token").value;
  $("#token").value = "";
  $("#unlock-error").textContent = "";
  load();
});
$("#refresh").addEventListener("click", load);
