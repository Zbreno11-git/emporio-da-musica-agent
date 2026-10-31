// Chat page: renders each turn from the API response only. Values, names and sources come from the server;
// this file formats and places them (rules in format.js). Data never goes through innerHTML.
import { priceView, sourcesView, traceLines } from "./format.js";

const $ = (selector) => document.querySelector(selector);
const log = $("#log");
const form = $("#composer");
const input = $("#message");
const sendButton = $("#send");
const statusRegion = $("#status");
const opening = $("#opening");
const profileLabel = $("#profile-label");

let pending = false;
let lastQuestion = "";

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === false || value == null) continue;
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) {
    if (child == null || child === false) continue;
    node.append(child instanceof Node ? child : String(child));
  }
  return node;
}

const clock = () => new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

function requestId() {
  if (crypto.randomUUID) return crypto.randomUUID();
  const b = crypto.getRandomValues(new Uint8Array(16));
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const h = [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, { credentials: "same-origin", headers: { "Content-Type": "application/json" }, ...options });
  } catch {
    return { status: 0, ok: false, body: { code: "network", retryable: true,
      message: "Não consegui falar com a loja agora. Confira a conexão e tente de novo." } };
  }
  let body = null;
  try { body = await response.json(); } catch { body = null; }
  if (!response.ok && !body?.message) {
    body = { code: "unexpected", retryable: true, message: "Algo saiu errado do nosso lado. Quer tentar de novo?" };
  }
  return { status: response.status, ok: response.ok, body };
}

const startSession = () => api("/api/session", { method: "POST" });
let sessionReady = startSession(); // a send waits for it, so the first message never races the cookie

function announce(text) {
  statusRegion.textContent = text;
}

function scrollToTurn(node) {
  node.scrollIntoView({ block: "nearest", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}

function avatar() {
  return el("img", { class: "avatar", src: "/static/symbol.svg", alt: "", width: 40, height: 40 });
}

function addUser(text) {
  const turn = el("div", { class: "turn turn-user" },
    el("div", { class: "turn-body" },
      el("p", { class: "bubble" }, el("span", { class: "visually-hidden" }, "Você: "), text),
      el("span", { class: "time" }, clock())));
  log.append(turn);
  scrollToTurn(turn);
}

function addNotice(text) {
  const node = el("p", { class: "notice" }, text);
  log.append(node);
  scrollToTurn(node);
  return node;
}

function productCard(card) {
  const view = priceView(card);
  const price = el("div", { class: `price-block${view.available ? "" : " unavailable-price"}` });
  if (view.payment) {
    price.append(el("span", { class: "price" }, view.payment.amount),
                 el("span", { class: "price-note" }, view.payment.label));
    if (view.list) price.append(el("span", { class: "price-list" }, el("s", {}, view.list), " ", el("span", { class: "price-off" }, view.percent)));
    else if (card.payment_cents !== card.offer_cents) price.append(el("span", { class: "price-note" }, `Preço: ${view.current}`));
  } else if (view.available) {
    if (view.list) price.append(el("span", { class: "price-list" }, el("s", {}, view.list), " ", el("span", { class: "price-off" }, view.percent)));
    price.append(el("span", { class: "price" }, view.current));
  } else {
    price.append(el("span", { class: "price-note" }, "Preço de tabela"), el("span", { class: "price" }, view.current));
  }
  return el("li", { class: "product-card", "data-product-id": card.product_id },
    el("img", { src: "/static/symbol.svg", alt: "", width: 56, height: 56, loading: "lazy" }),
    el("div", {},
      el("p", { class: "product-name" }, card.name),
      el("p", { class: "product-attr" }, card.attribute),
      el("span", { class: `availability${view.available ? "" : " unavailable"}` }, view.availability)),
    price);
}

function handoffBox(handoff) {
  const feedback = el("span", { role: "status", class: "note" });
  const copy = el("button", { type: "button", class: "button button-secondary", onclick: async () => {
    try {
      await navigator.clipboard.writeText(handoff.summary);
      feedback.textContent = " Resumo copiado.";
    } catch {
      feedback.textContent = " Não deu para copiar automaticamente; selecione o texto acima.";
    }
  } }, "Copiar resumo");
  return el("section", { class: "handoff extra", "aria-label": "Resumo para a equipe da loja" },
    el("h2", {}, "Resumo preparado para a equipe"),
    el("p", {}, handoff.summary),
    el("p", { class: "note" }, `Ainda não foi enviado. Para falar com a equipe, copie e mande pelo ${handoff.channel_label}: ${handoff.destination}.`),
    el("div", {}, copy, feedback));
}

async function profilePicker(reason) {
  const box = el("div", { class: "picker extra" }, el("p", {}, reason));
  const res = await api("/api/demo-profiles");
  if (!res.ok) {
    box.append(el("p", { class: "note" }, res.body.message));
    return box;
  }
  const options = el("div", { class: "picker-options" });
  for (const profile of res.body.profiles) {
    options.append(el("button", { type: "button", class: "button button-secondary", onclick: () => chooseProfile(profile, box) }, profile.label));
  }
  box.append(options);
  return box;
}

async function chooseProfile(profile, box) {
  const res = await api("/api/session/profile", { method: "POST", body: JSON.stringify({ profile: profile.alias }) });
  if (!res.ok) {
    addNotice(res.body.message);
    return;
  }
  box.replaceChildren(el("p", { class: "note" }, `Perfil escolhido: ${res.body.label}`));
  profileLabel.textContent = res.body.label;
  addNotice(`Agora você está como ${res.body.label}. A conversa recomeça com esse perfil; as mensagens acima não são mais usadas.`);
  if (lastQuestion && !input.value) input.value = lastQuestion;
  input.focus();
}

function addAgent(body) {
  const parts = [el("p", { class: "bubble" }, el("span", { class: "visually-hidden" }, "Loja: "), body.text),
                 el("span", { class: "time" }, clock())];
  if (body.cards.length) parts.push(el("ul", { class: "cards", "aria-label": "Produtos" }, body.cards.map(productCard)));
  if (body.handoff) parts.push(handoffBox(body.handoff));
  const links = el("div", { class: "turn-links" });
  const sources = sourcesView(body.sources);
  if (sources.length) {
    links.append(el("details", { class: "extra sources" }, el("summary", {}, `Fontes (${sources.length})`),
      el("ul", {}, sources.map((s) => el("li", {}, s)))));
  }
  const tech = traceLines(body.trace);
  if (tech.length) {
    links.append(el("details", { class: "extra tech" }, el("summary", {}, "Detalhes técnicos"),
      el("ul", {}, tech.map((t) => el("li", {}, t)))));
  }
  if (links.childElementCount) parts.push(links);
  const turnBody = el("div", { class: "turn-body" }, parts);
  const turn = el("div", { class: "turn turn-agent", "data-next-action": body.next_action }, avatar(), turnBody);
  log.append(turn);
  if (body.next_action === "choose_profile") {
    profilePicker("Para ver pedidos, escolha um cliente de demonstração. A identidade vem desta escolha, nunca do chat.")
      .then((picker) => { turnBody.append(picker); scrollToTurn(picker); });
  }
  scrollToTurn(turn);
}

function addTyping() {
  const node = el("div", { class: "turn turn-agent typing-turn" }, avatar(),
    el("p", { class: "bubble typing" }, "Consultando a loja", el("span", { class: "dots", "aria-hidden": "true" }, el("i"), el("i"), el("i"))));
  log.append(node);
  scrollToTurn(node);
  announce("Consultando a loja…");
  return node;
}

function addError(body, retry) {
  const actions = el("div", { class: "error-actions" });
  const node = el("div", { class: "turn turn-agent", "data-error": body.code }, avatar(),
    el("div", { class: "turn-body" }, el("p", { class: "bubble error", role: "alert" }, body.message), actions));
  if (retry) {
    actions.append(el("button", { type: "button", class: "button", onclick: () => { node.remove(); retry(); } }, "Tentar novamente"));
  }
  log.append(node);
  scrollToTurn(node);
}

function setBusy(busy) {
  pending = busy;
  sendButton.disabled = busy;
  form.setAttribute("aria-busy", busy ? "true" : "false");
}

async function send(message, rid = requestId(), echo = true) {
  if (pending) return;
  setBusy(true);
  await sessionReady;
  opening.hidden = true;
  if (echo) {
    addUser(message);
    lastQuestion = message;
  }
  const typing = addTyping();
  const res = await api("/api/chat", { method: "POST", body: JSON.stringify({ request_id: rid, message }) });
  typing.remove();
  setBusy(false);
  if (res.ok) {
    addAgent(res.body);
    announce("Resposta recebida.");
    return;
  }
  announce("A resposta não chegou.");
  if (res.status === 410) {
    await startSession();
    profileLabel.textContent = "Visitante";
    addNotice("A conversa anterior expirou, então comecei uma nova. Sua pergunta voltou para o campo; é só enviar de novo.");
    if (!input.value) input.value = message;
    input.focus();
    return;
  }
  if (res.body.retryable) {
    addError(res.body, () => send(message, rid, false)); // same request_id: the server never answers twice
    return;
  }
  addError(res.body, null);
  if (!input.value) input.value = message; // keep the draft when retrying cannot help
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || pending) return;
  input.value = "";
  send(message);
});

document.querySelectorAll(".suggestion").forEach((button) => {
  button.addEventListener("click", () => send(button.dataset.message));
});

$("#change-profile").addEventListener("click", async () => {
  opening.hidden = true;
  const picker = await profilePicker("Escolha um cliente de demonstração. Trocar de perfil recomeça a conversa.");
  log.append(picker);
  scrollToTurn(picker);
});

$("#new-conversation").addEventListener("click", async () => {
  await api("/api/session", { method: "DELETE" });
  sessionReady = startSession();
  await sessionReady;
  log.replaceChildren();
  profileLabel.textContent = "Visitante";
  lastQuestion = "";
  opening.hidden = false;
  input.value = "";
  input.focus();
  announce("Nova conversa iniciada.");
});

