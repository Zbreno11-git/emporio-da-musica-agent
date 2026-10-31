"""One customer turn: Gemini decides which tool to call; the backend validates, executes and composes.

Flow per turn (guide 02 §6):
1. Build the conversation from this session's own history (the SDK's content objects, including thought
   signatures, are kept as returned) plus the new message.
2. Up to `max_rounds` rounds of tool calls, `max_tool_calls` executions and `max_model_calls` generations,
   all under one deadline. Identical calls within a turn reuse the first result.
3. Compose the response: text from the model; cards, values and sources hydrated by the backend from this
   turn's tool results.
4. Check the text before showing it (D22): every R$ amount, percentage, brand + model and model code must come
   from evidence, and no action may be claimed as done or promised. One corrective round is allowed (it may call
   a tool to fetch missing evidence); otherwise a deterministic fallback is used.
"""

from __future__ import annotations

import re
import sqlite3
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, Protocol

from google.genai import types
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app import prompts
from app.config import Settings
from app.tools import catalog as catalog_tool
from app.tools import orders as orders_tool
from app.tools import quote as quote_tool
from app.tools.policies import PolicyIndex


# --- errors ------------------------------------------------------------------------------------------

class ProviderUnavailable(Exception):
    """The model provider failed or rate-limited us; the turn produced no answer."""


class DeadlineExceeded(Exception):
    """The turn did not finish within the configured deadline."""


# --- model client ------------------------------------------------------------------------------------

@dataclass
class ModelReply:
    content: types.Content
    calls: list[types.FunctionCall]
    text: str
    usage: dict[str, int]


class LLM(Protocol):
    model: str

    def generate(self, *, system: str, contents: list[types.Content], tools: list[types.Tool],
                 timeout_s: float, allow_tools: bool) -> ModelReply: ...


def _usage(meta: Any) -> dict[str, int]:
    if meta is None:
        return {}
    fields = {"prompt_token_count": "input", "candidates_token_count": "output",
              "thoughts_token_count": "thoughts", "total_token_count": "total"}
    return {v: getattr(meta, k) or 0 for k, v in fields.items()}


class GeminiLLM:
    def __init__(self, api_key: str, model: str, thinking_level: str = ""):
        from google import genai

        if not api_key or not model:
            raise ValueError("GEMINI_API_KEY and GEMINI_MODEL are required")
        self.model = model
        self._client = genai.Client(api_key=api_key)
        self._thinking = types.ThinkingConfig(thinking_level=thinking_level) if thinking_level else None

    def generate(self, *, system, contents, tools, timeout_s, allow_tools) -> ModelReply:
        from google.genai import errors
        import httpx

        config = types.GenerateContentConfig(
            system_instruction=system,
            tools=tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig(
                mode="AUTO" if allow_tools else "NONE")),
            http_options=types.HttpOptions(timeout=max(1000, int(timeout_s * 1000)),
                                           retry_options=types.HttpRetryOptions(attempts=1)),
            thinking_config=self._thinking,
        )
        try:
            resp = self._client.models.generate_content(model=self.model, contents=contents, config=config)
        except errors.APIError as exc:
            raise ProviderUnavailable(f"provider error {exc.code}") from exc
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise DeadlineExceeded("model call timed out") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(f"transport error: {type(exc).__name__}") from exc
        candidate = (resp.candidates or [None])[0]
        content = candidate.content if candidate is not None and candidate.content is not None else \
            types.Content(role="model", parts=[])
        content.role = content.role or "model"
        calls = [p.function_call for p in (content.parts or []) if p.function_call]
        text = "".join(p.text for p in (content.parts or []) if p.text and not p.thought).strip()
        return ModelReply(content=content, calls=calls, text=text, usage=_usage(resp.usage_metadata))


# --- tools ---------------------------------------------------------------------------------------------

class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QueryCatalogArgs(_Args):
    sql: str = Field(max_length=catalog_tool.MAX_SQL_CHARS, description="One SQLite SELECT returning product_id.")
    params: list[int | float | str] = Field(default_factory=list, max_length=catalog_tool.MAX_PARAMS,
                                            description="Positional values for the ? placeholders.")
    intent: Literal["discover", "lookup", "compare"]
    limit: int | None = Field(default=None, ge=1, le=catalog_tool.MAX_PRODUCTS,
                              description="How many products the customer asked to see, if they said.")


class QuoteProductArgs(_Args):
    product_id: int = Field(gt=0)
    method: Literal["table", "pix", "debit", "credit", "boleto"]
    installments: int = Field(default=1, ge=1, le=12, description="Only for credit; 1 otherwise.")


class GetMyOrderArgs(_Args):
    order_id: int = Field(gt=0, description="The order number the customer mentioned.")


class SearchPolicyArgs(_Args):
    question: str = Field(min_length=2, max_length=500,
                          description="Short question in Portuguese about a store rule; rephrase to search again.")


class PrepareHandoffArgs(_Args):
    reason: Literal["policy_gap", "policy_conflict", "complaint", "requires_staff"]
    summary: str = Field(min_length=10, max_length=300,
                         description="One line in Portuguese for the store team: the case and the open point.")


@dataclass
class ToolSpec:
    name: str
    description: str
    args: type[_Args]
    run: Callable[["TurnState", Any], dict]

    def declaration(self) -> types.FunctionDeclaration:
        schema = self.args.model_json_schema()
        return types.FunctionDeclaration(name=self.name, description=self.description,
                                         parameters_json_schema=schema)


@dataclass
class ToolRun:
    name: str
    args: dict
    result: dict
    ok: bool
    ms: int


@dataclass
class TurnState:
    """Everything a tool may see. The customer identity is frozen here by the server, never by the model."""
    settings: Settings
    message: str
    known_products: dict[int, str]  # session memory: product_id -> name (from earlier tool results)
    customer_id: int | None = None
    policy_index: PolicyIndex | None = None
    runs: list[ToolRun] = field(default_factory=list)
    catalog_results: list[list[dict]] = field(default_factory=list)
    quotes: list[dict] = field(default_factory=list)
    orders: list[dict] = field(default_factory=list)
    policy_results: list[dict] = field(default_factory=list)
    profile_required: bool = False
    handoff: dict | None = None


def _run_query_catalog(state: TurnState, args: QueryCatalogArgs) -> dict:
    try:
        result = catalog_tool.query_catalog(state.settings.catalog_db, args.sql, args.params, args.intent,
                                            state.message, args.limit)
    except catalog_tool.CatalogQueryError as exc:
        return {"ok": False, **exc.to_dict()}
    products = []
    for p in result.products:
        state.known_products[p["product_id"]] = p["name"]
        products.append({k: p[k] for k in ("product_id", "name", "category", "attribute", "availability",
                                            "base_cents", "discount_percent", "offer_cents", "pix_cents")}
                        | {"description": p["description"][:200], "specs": p["specs"]})
    state.catalog_results.append(result.products)
    return {"ok": True, "products": products, "dropped_unavailable": result.dropped_unavailable,
            "dropped_over_budget": result.dropped_over_budget,
            "dropped_other_strings": result.dropped_other_strings,
            "note": "" if products else (
                "No products matched THIS query. That does not mean the store has none: never say the store "
                "lacks a kind of instrument from this result; query again by category_id. Sellable products per "
                "category: " + "; ".join(f"{k}: {v}" for k, v in
                                         catalog_tool.available_by_category(state.settings.catalog_db).items()))}


def _product_row(db: Path, product_id: int) -> sqlite3.Row | None:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return con.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
    finally:
        con.close()


def _run_quote_product(state: TurnState, args: QuoteProductArgs) -> dict:
    if args.product_id not in state.known_products:
        return {"ok": False, "error": "unknown_product",
                "message": "Use a product_id returned by query_catalog in this conversation."}
    row = _product_row(state.settings.catalog_db, args.product_id)
    if row is None:
        return {"ok": False, "error": "unknown_product", "message": "Product not found."}
    q = quote_tool.quote(product_id=row["product_id"], status=row["status"], stock_quantity=row["stock_quantity"],
                         base_cents=row["base_cents"], promotion_percent=row["promotion_percent"],
                         method=args.method, installments=args.installments)
    result = {"ok": True, "name": row["name"], **q.to_dict()}
    state.quotes.append(result)
    return result


def _run_get_my_order(state: TurnState, args: GetMyOrderArgs) -> dict:
    result = orders_tool.get_order(state.settings.orders_db, state.customer_id, args.order_id)
    if result.get("error") == "profile_required":
        state.profile_required = True
    elif result.get("found"):
        state.orders.append(result)
    return result


def _run_search_policy(state: TurnState, args: SearchPolicyArgs) -> dict:
    sections = state.policy_index.search(args.question)
    for s in sections:
        if s["section_id"] not in {p["section_id"] for p in state.policy_results}:
            state.policy_results.append(s)
    return {"ok": True, "manual_version": state.policy_index.manual_version, "sections": sections,
            "note": "No section matched; try other words." if not sections else ""}


def _run_prepare_handoff(state: TurnState, args: PrepareHandoffArgs) -> dict:
    state.handoff = {"reason": args.reason, "summary": args.summary,
                     "channel_label": "WhatsApp de atendimento (manual da loja, seção 7)",
                     "destination": state.policy_index.whatsapp_channel(), "delivery_status": "prepared"}
    return {"ok": True, "delivery_status": "prepared", "destination": state.handoff["destination"],
            "note": "Nothing was sent. The interface shows the summary for the customer to take to the store's "
                    "WhatsApp. Do not say the team was notified."}


TOOLS: dict[str, ToolSpec] = {
    "query_catalog": ToolSpec(
        "query_catalog",
        "Find products in the store catalog with one read-only SQLite SELECT that returns product_id. "
        "The backend hydrates names, prices and availability from the canonical table.\n"
        + catalog_tool.SCHEMA_DESCRIPTION,
        QueryCatalogArgs, _run_query_catalog),
    "quote_product": ToolSpec(
        "quote_product",
        "Price of a known product for a payment method (table, pix, debit, credit, boleto) and, for credit, "
        "an installment count. Applies the store rules for promotions, PIX and installments and returns the "
        "decision (allowed, rejected, needs_confirmation, unavailable) with the manual sections used.",
        QuoteProductArgs, _run_quote_product),
    "get_my_order": ToolSpec(
        "get_my_order",
        "Status, items, recorded total, payment method and tracking of an order of the customer's selected demo "
        "profile. The profile comes from the session; only the order number is passed.",
        GetMyOrderArgs, _run_get_my_order),
    "search_policy": ToolSpec(
        "search_policy",
        "Search the store manual (v2.1) by section: hours, contacts, payment and installments, returns, "
        "exchanges, warranty, shipping, tracking, promotions, service rules, privacy. Returns up to 3 sections "
        "plus linked ones, with section id, title, pages and text.",
        SearchPolicyArgs, _run_search_policy),
    "prepare_handoff": ToolSpec(
        "prepare_handoff",
        "Prepare a one-line summary for the store team when the manual is silent or contradictory on the "
        "decisive point, for complaints, or when only staff can decide. It sends nothing.",
        PrepareHandoffArgs, _run_prepare_handoff),
}


# --- text checks ---------------------------------------------------------------------------------------

_MONEY_RE = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*|\d+)(?:,(\d{1,2}))?")
_PERCENT_RE = re.compile(r"(\d{1,3})\s*%")
_CLAIM_RE = re.compile(
    r"\b(registrei|registramos|j[aá] registrei|protocolo\s*(n[ºo°]|n[uú]mero)?\s*\d|reservei|reservamos|"
    r"reembolso\s+(foi\s+)?(feito|realizado|aprovado|efetuado)|estorno\s+(feito|realizado|aprovado)|"
    r"pedido\s+(foi\s+)?cancelado\s+por\s+mim|cancelei|encaminhei|j[aá]\s+avisei\s+a\s+equipe)\b",
    re.IGNORECASE)


# Promises of actions no integration performs (watch stock, notify, hold an item or a price).
_PROMISE_RE = re.compile(
    r"\b(fico de olho|ficar de olho|fico atent[oa]|te aviso|te avisar|vou avisar|aviso (assim que|quando)|"
    r"posso separar|vou separar|separo (um|uma|o|a) |posso reservar|vou reservar|reservo|"
    r"(seguro|garanto|congelo) o pre[cç]o)\b", re.IGNORECASE)


def money_mentions(text: str) -> list[int]:
    out = []
    for whole, frac in _MONEY_RE.findall(text):
        out.append(int(whole.replace(".", "")) * 100 + int((frac or "0").ljust(2, "0")))
    return out


def brl(cents: int) -> str:
    whole, frac = divmod(cents, 100)
    return f"R$ {whole:,}".replace(",", ".") + f",{frac:02d}"


def _evidence_values(state: TurnState, context_cents: set[int]) -> tuple[set[int], set[int]]:
    cents, pcts = set(context_cents), {quote_tool.PIX_DISCOUNT_PERCENT}
    for products in state.catalog_results:
        for p in products:
            cents |= {p["base_cents"], p["offer_cents"], p["pix_cents"]}
            pcts.add(p["discount_percent"])
    for q in state.quotes:
        cents |= {v for v in (q["base_cents"], q["offer_cents"], q["payment_cents"]) if v}
        cents |= set(q["installment_cents"])
        pcts.add(q["discount_percent"])
    for o in state.orders:
        cents.add(o["total_cents"])
    for s in state.policy_results:
        cents |= set(money_mentions(s["text"]))
        pcts |= {int(x) for x in _PERCENT_RE.findall(s["text"])}
    cents |= set(money_mentions(state.message))
    pcts |= {int(x) for x in _PERCENT_RE.findall(state.message)}
    return cents, pcts


# Brands the store sells (a test checks every catalog name contains one) plus common market brands a model might
# suggest. A brand followed by a model word is a product reference and needs evidence; a bare brand does not.
BRANDS = (
    "Crafter", "Fender", "Giannini", "Gibson", "Ibanez", "Kala", "Kalani", "Korg", "Martin", "Music Man", "Nord",
    "Ohana", "PRS", "Pearl", "Roland", "Rozini", "Shelby", "Tagima", "Takamine", "Taylor", "Yamaha",
    # not in the catalog
    "Alesis", "Behringer", "Boss", "Casio", "Condor", "Cort", "Di Giorgio", "Eagle", "Epiphone", "ESP", "Gretsch",
    "Hofner", "Jackson", "Kawai", "Ludwig", "Mapex", "Marshall", "Memphis", "Michael", "Orange", "Schecter",
    "Sonor", "Squier", "Sterling", "Strinberg", "Tama", "Vox", "Waldman", "Warwick", "Washburn",
)
_BRAND_REF_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, BRANDS), key=len, reverse=True))
                           + r")\s+([A-Z0-9][\w-]*)")
_MODEL_CODE_RE = re.compile(r"\b(?=[\w-]*[A-Z])(?=[\w-]*\d)[A-Z0-9][\w-]{2,}\b")  # GD20, C40, KAL-700T, GSR200
_INSTALLMENTS_RE = re.compile(r"^\d+X$")
_TOKEN_RE = re.compile(r"[\w-]+")


def product_reference_problems(text: str, evidence: str) -> list[str]:
    """Every brand + model or model code in the text must appear in the evidence (tool results, customer words)."""
    ev = " ".join(evidence.split()).casefold()
    tokens = set(_TOKEN_RE.findall(ev))
    problems = []
    for m in _BRAND_REF_RE.finditer(text):
        ref = f"{m.group(1)} {m.group(2)}"
        if not re.search(r"(?<!\w)" + re.escape(ref.casefold()) + r"(?!\w)", ev):
            problems.append(f"names a product without a tool result in this conversation: '{ref}'")
    for code in _MODEL_CODE_RE.findall(text):
        if not _INSTALLMENTS_RE.match(code) and code.casefold() not in tokens:
            problems.append(f"names a model without a tool result in this conversation: '{code}'")
    return problems


# Sound and build qualities a customer relies on when choosing. Each one in the text must appear in the description or
# specs of a product from this conversation (accent-insensitive stems). Real case: "timbre bem definido" for a guitar
# whose description only mentions "projeção sonora" (capture of 2026-10-31).
QUALITY_STEMS = ("timbre", "sonoridade", "encorpad", "projec", "sustain", "graves", "agudos", "brilhant", "aveludad",
                 "quente", "resistent", "duravel", "durabilidade", "robust", "confortavel", "conforto")
_WORD_RE = re.compile(r"[a-z]+")


def _fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def quality_problems(text: str, product_facts: str) -> list[str]:
    facts = _fold(product_facts)
    claimed = {stem for word in _WORD_RE.findall(_fold(text)) for stem in QUALITY_STEMS if word.startswith(stem)}
    return [f"describes a quality that is not in the product data: '{stem}'" for stem in sorted(claimed)
            if stem not in facts]


def _product_facts(state: TurnState) -> str:
    """Descriptions and specs of every product seen in this conversation, read from the catalog."""
    if not state.known_products:
        return ""
    rows = catalog_tool.hydrate(state.settings.catalog_db, list(state.known_products))
    return "\n".join(f"{p['description']} {' '.join(map(str, p['specs'].values()))}" for p in rows)


def _evidence_text(state: TurnState) -> str:
    parts = [state.message, *state.known_products.values()]
    parts += [p["name"] for products in state.catalog_results for p in products]
    for o in state.orders:
        parts += [str(o.get("tracking_code") or ""), *(i["name"] for i in o.get("items", []))]
    parts += [s["text"] for s in state.policy_results]
    return "\n".join(parts)


def check_text(text: str, state: TurnState, context_cents: set[int]) -> list[str]:
    cents, pcts = _evidence_values(state, context_cents)
    problems = [f"amount {brl(v)} has no evidence" for v in money_mentions(text) if v not in cents]
    problems += [f"percentage {p}% has no evidence" for p in map(int, _PERCENT_RE.findall(text)) if p not in pcts]
    problems += [f"claims an action that was not executed: '{m.group(0)}'" for m in _CLAIM_RE.finditer(text)]
    problems += [f"promises an action no system performs: '{m.group(0)}'" for m in _PROMISE_RE.finditer(text)]
    problems += product_reference_problems(text, _evidence_text(state))
    problems += quality_problems(text, _product_facts(state))
    return problems


# --- response composition ------------------------------------------------------------------------------

_METHOD_LABEL = {"pix": "no PIX", "debit": "no débito", "boleto": "no boleto", "table": "", "credit": "no cartão"}


def build_cards(state: TurnState) -> list[dict]:
    if state.quotes:
        latest: dict[int, dict] = {}
        for q in state.quotes:
            latest[q["product_id"]] = q
        cards = []
        for q in latest.values():
            base = catalog_tool.hydrate(state.settings.catalog_db, [q["product_id"]])[0]
            card = _card(base)
            if q["decision"] in ("allowed", "needs_confirmation") and q["payment_cents"]:
                card |= {"payment_cents": q["payment_cents"], "payment_method": q["method"]}
                if q["method"] == "credit" and q["installments"] > 1:
                    card |= {"installments": q["installments"], "installment_cents": q["installment_cents"][0]}
            cards.append(card)
        return cards
    if state.catalog_results:
        return [_card(p) for p in state.catalog_results[-1]][: catalog_tool.DEFAULT_DISCOVER_CARDS]
    return []


def _card(p: dict) -> dict:
    available = p["availability"] == "available"
    return {"product_id": p["product_id"], "name": p["name"], "attribute": p["attribute"],
            "availability": p["availability"], "base_cents": p["base_cents"],
            "offer_cents": p["offer_cents"] if available else p["base_cents"],
            "discount_percent": p["discount_percent"] if available else 0}


def fallback_text(cards: list[dict]) -> str:
    """Deterministic answer from validated card data, used only when the model's text fails the checks."""
    if not cards:
        return "Não consegui confirmar essa informação agora. Pode tentar de novo em instantes?"
    parts = []
    for c in cards:
        if c["availability"] != "available":
            parts.append(f"O {c['name']} está indisponível no momento.")
        elif c.get("payment_cents"):
            label = _METHOD_LABEL.get(c.get("payment_method") or "", "")
            parts.append(f"O {c['name']} sai por {brl(c['payment_cents'])} {label}".strip() + ".")
        elif c["discount_percent"]:
            parts.append(f"O {c['name']} está por {brl(c['offer_cents'])} "
                         f"({c['discount_percent']}% de desconto sobre {brl(c['base_cents'])}).")
        else:
            parts.append(f"O {c['name']} está por {brl(c['offer_cents'])}.")
    return " ".join(parts)


# --- the turn ------------------------------------------------------------------------------------------

@dataclass
class TurnResult:
    text: str
    cards: list[dict]
    sources: list[dict]
    next_action: str
    handoff: dict | None
    contents: list[types.Content]  # this turn's content, appended to the session history on success
    trace: dict
    known_products: dict[int, str]


class Agent:
    def __init__(self, settings: Settings, llm: LLM, tools: dict[str, ToolSpec] | None = None,
                 policy_index: PolicyIndex | None = None):
        self.settings = settings
        self.llm = llm
        self.tools = tools or TOOLS
        self.policy_index = policy_index or PolicyIndex.load(settings.policy_index)
        self.policy_index.whatsapp_channel()  # fail at startup, not in a customer turn
        self._tool_decl = [types.Tool(function_declarations=[t.declaration() for t in self.tools.values()])]

    def run_turn(self, *, message: str, history: list[types.Content], known_products: dict[int, str],
                 context_cents: set[int], customer_id: int | None = None,
                 context_lines: list[str] | None = None) -> TurnResult:
        s = self.settings
        started = time.monotonic()
        deadline = started + s.chat_timeout_s
        state = TurnState(settings=s, message=message, known_products=dict(known_products), customer_id=customer_id,
                          policy_index=self.policy_index)
        user = types.Content(role="user", parts=[types.Part(text=message)])
        turn_contents: list[types.Content] = [user]
        system = prompts.system_instruction(context_lines or [])
        model_calls = rounds = 0
        usage_total: dict[str, int] = {}
        cache: dict[str, dict] = {}
        text = ""

        def remaining() -> float:
            left = deadline - time.monotonic()
            if left <= 0.5:
                raise DeadlineExceeded("turn deadline reached")
            return left

        def generate(allow_tools: bool) -> ModelReply:
            nonlocal model_calls
            model_calls += 1
            reply = self.llm.generate(system=system, contents=history + turn_contents, tools=self._tool_decl,
                                      timeout_s=remaining(), allow_tools=allow_tools)
            for k, v in reply.usage.items():
                usage_total[k] = usage_total.get(k, 0) + v
            turn_contents.append(reply.content)
            return reply

        reply = generate(allow_tools=True)
        while reply.calls:
            rounds += 1
            responses = []
            for call in reply.calls:
                responses.append(self._execute(call, state, cache, remaining))
            turn_contents.append(types.Content(role="user", parts=responses))
            budget_left = (rounds < s.max_rounds and len(state.runs) < s.max_tool_calls
                           and model_calls < s.max_model_calls - 1)
            reply = generate(allow_tools=budget_left)
            if not budget_left:
                break
        text = reply.text

        cards = build_cards(state)
        problems = check_text(text, state, context_cents) if text else ["empty answer"]
        # The history keeps only the answer that is actually shown, in place of a rejected one.
        kept = turn_contents[:-1]
        corrected = False
        if problems and model_calls < s.max_model_calls and deadline - time.monotonic() > 3:
            note = ("[server check] Your previous answer cannot be shown: " + "; ".join(problems) +
                    ". If a value or product needs confirmation, call the tool for it now; otherwise remove it. "
                    "Rewrite the answer in Brazilian Portuguese using only values, products and characteristics "
                    "from the tool results, without claiming or promising actions you did not execute.")
            turn_contents.append(types.Content(role="user", parts=[types.Part(text=note)]))
            # Missing evidence can be fetched: the correction may run one more tool round, budget permitting.
            can_fetch = model_calls < s.max_model_calls - 1 and len(state.runs) < s.max_tool_calls
            reply = generate(allow_tools=can_fetch)
            if reply.calls and can_fetch:
                rounds += 1
                turn_contents.append(types.Content(role="user", parts=[
                    self._execute(call, state, cache, remaining) for call in reply.calls]))
                reply = generate(allow_tools=False)
                cards = build_cards(state)
            text, corrected = reply.text, True
            problems = check_text(text, state, context_cents) if text else ["empty answer"]
        fallback = bool(problems)
        if fallback:
            text = fallback_text(cards)
            final = types.Content(role="model", parts=[types.Part(text=text)])
        else:
            final = reply.content

        sources = [{"type": "catalog", "id": f"product:{c['product_id']}", "label": "Catálogo da loja"} for c in cards]
        sources += [{"type": "order", "id": f"order:{o['order_id']}", "label": f"Pedido {o['order_id']}"}
                    for o in state.orders]
        cited = [q_rule for q in state.quotes for q_rule in q["rule_ids"]]
        cited += [p["section_id"] for p in state.policy_results if not p["related"]][:3]
        for rule in cited:
            section = self.policy_index.by_id.get(rule, {})
            src = {"type": "policy", "id": rule, "label": f"Manual da loja, seção {rule}",
                   "page_start": section.get("page_start"), "page_end": section.get("page_end")}
            if src not in sources:
                sources.append(src)
        if state.profile_required:
            next_action = "choose_profile"
        elif state.handoff:
            next_action = "contact_store"
        elif not cards and text.rstrip().endswith("?"):
            next_action = "clarify"
        else:
            next_action = "none"
        trace = {
            "model": self.llm.model,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "model_calls": model_calls,
            "tool_rounds": rounds,
            "tools": [{"name": r.name, "args": r.args, "ok": r.ok, "ms": r.ms} for r in state.runs],
            "usage": usage_total,
            "text_corrected": corrected,
            "text_fallback": fallback,
            "check_problems": problems,
        }
        return TurnResult(text=text, cards=cards, sources=sources, next_action=next_action, handoff=state.handoff,
                          contents=kept + [final], trace=trace, known_products=state.known_products)

    def _execute(self, call: types.FunctionCall, state: TurnState, cache: dict[str, dict],
                 remaining: Callable[[], float]) -> types.Part:
        remaining()
        name, raw_args = call.name or "", dict(call.args or {})
        key = f"{name}:{sorted(raw_args.items())!r}"
        started = time.monotonic()
        spec = self.tools.get(name)
        if key in cache:
            result = cache[key] | {"note": "same call already answered in this turn"}
        elif spec is None:
            result = {"ok": False, "error": "unknown_tool", "message": f"No tool named {name!r}."}
        elif len(state.runs) >= self.settings.max_tool_calls:
            result = {"ok": False, "error": "tool_budget", "message": "Tool budget for this turn is used up."}
        else:
            try:
                result = spec.run(state, spec.args.model_validate(raw_args))
            except ValidationError as exc:
                result = {"ok": False, "error": "invalid_arguments",
                          "message": "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors())}
            cache[key] = result
            state.runs.append(ToolRun(name, raw_args, result, bool(result.get("ok")),
                                      int((time.monotonic() - started) * 1000)))
        return types.Part(function_response=types.FunctionResponse(id=call.id, name=name, response=result))

