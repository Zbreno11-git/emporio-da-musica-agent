"""HTTP layer (guide 02 §7): static chat page, session cookie, chat turn, health check and public errors."""

from __future__ import annotations

import hmac
import json
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.agent import Agent, DeadlineExceeded, GeminiLLM, LLM, ProviderUnavailable
from app.config import Settings, get_settings
from app.contracts import ChatRequest, ChatResponse, ProfileRequest
from app.metrics import TurnMetrics
from app.session import CachedRequest, DailyTurnCap, SessionStore
from app.tools import orders as orders_tool

COOKIE = "emporio_sid"
STATIC = Path(__file__).resolve().parent / "static"


def error(status: int, code: str, message: str, retryable: bool, request_id: str | None = None) -> JSONResponse:
    body = {"code": code, "message": message, "retryable": retryable}
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(body, status_code=status)


def create_app(settings: Settings | None = None, llm: LLM | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Empório da Música agent", docs_url=None, redoc_url=None)
    store = SessionStore(settings.session_ttl_s, settings.max_sessions)
    daily_cap = DailyTurnCap(settings.max_turns_per_day)
    state = {"agent": Agent(settings, llm) if llm else None}
    metrics = TurnMetrics(*_model_price(settings))
    app.state.metrics = metrics  # read by tests; never holds customer text (app/metrics.py)

    def agent() -> Agent:
        if state["agent"] is None:
            state["agent"] = Agent(settings, GeminiLLM(settings.gemini_api_key, settings.gemini_model,
                                                       settings.thinking_level))
        return state["agent"]

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, exc: RequestValidationError):
        return error(422, "invalid_input", "A mensagem precisa ter entre 1 e 2000 caracteres.", False)

    def same_origin(request: Request) -> bool:
        origin = request.headers.get("origin")
        if not origin:
            return True
        return urlparse(origin).netloc == request.headers.get("host")

    def set_cookie(request: Request, response: Response, sid: str) -> None:
        secure = request.headers.get("x-forwarded-proto", request.url.scheme) == "https"
        response.set_cookie(COOKIE, sid, httponly=True, samesite="lax", secure=secure,
                            max_age=settings.session_ttl_s)

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    # Cloud Run's front end reserves paths ending in "z", so the hosted check is /health; /healthz stays for local use.
    @app.get("/health")
    @app.get("/healthz")
    def healthz():
        try:
            manifest = json.loads((settings.data_dir / "manifest.json").read_text())
            ready = all(p.exists() for p in (settings.catalog_db, settings.orders_db, settings.policy_index))
        except (OSError, ValueError):
            ready, manifest = False, {}
        if not ready:
            return JSONResponse({"status": "not_ready"}, status_code=503)
        return {"status": "ok", "dataset_id": manifest.get("dataset_id"), "model": settings.gemini_model}

    @app.post("/api/session", status_code=201)
    def new_session(request: Request):
        if not same_origin(request):
            return error(403, "forbidden_origin", "Origem não permitida.", False)
        session = store.create()
        if session is None:
            return error(429, "too_many_sessions", "Muitas conversas abertas agora. Tente de novo em instantes.", True)
        response = JSONResponse({"profile": None}, status_code=201)
        set_cookie(request, response, session.id)
        return response

    @app.delete("/api/session", status_code=204)
    def end_session(request: Request):
        store.delete(request.cookies.get(COOKIE))
        response = Response(status_code=204)
        response.delete_cookie(COOKIE)
        return response

    @app.get("/api/demo-profiles")
    def demo_profiles(request: Request):
        if store.get(request.cookies.get(COOKIE)) is None:
            return error(410, "session_expired", "A conversa expirou. Vamos começar uma nova?", True)
        return {"profiles": orders_tool.list_profiles(settings.orders_db)}

    @app.post("/api/session/profile")
    def choose_profile(body: ProfileRequest, request: Request):
        if not same_origin(request):
            return error(403, "forbidden_origin", "Origem não permitida.", False)
        session = store.get(request.cookies.get(COOKIE))
        if session is None:
            return error(410, "session_expired", "A conversa expirou. Vamos começar uma nova?", True)
        customer_id = orders_tool.resolve_profile(settings.orders_db, body.profile)
        if customer_id is None:
            return error(422, "invalid_profile", "Perfil de demonstração desconhecido.", False)
        # New identity, new context: history, cached answers and in-flight turns of the old profile are dropped.
        session.reset_context()
        session.profile_alias, session.customer_id = body.profile, customer_id
        new_id = store.rotate(session)
        label = next(p["label"] for p in orders_tool.list_profiles(settings.orders_db) if p["alias"] == body.profile)
        response = JSONResponse({"profile": body.profile, "label": label})
        set_cookie(request, response, new_id)
        return response

    @app.post("/api/chat")
    def chat(body: ChatRequest, request: Request):
        rid = str(body.request_id)
        if not same_origin(request):
            return error(403, "forbidden_origin", "Origem não permitida.", False, rid)
        session = store.get(request.cookies.get(COOKIE))
        if session is None:
            return error(410, "session_expired", "A conversa expirou. Vamos começar uma nova?", True, rid)

        cached = session.requests.get(rid)
        if cached is not None:
            if cached.message != body.message:
                return error(409, "request_id_reused", "Este identificador já foi usado com outra mensagem.", False, rid)
            if cached.status == "done":
                return cached.response
            return error(409, "in_progress", "Ainda estou respondendo essa mensagem.", True, rid)
        if not session.lock.acquire(blocking=False):
            return error(409, "turn_in_progress", "Espere a resposta anterior terminar.", True, rid)
        try:
            if not session.allow_turn(settings.turns_per_minute, time.monotonic()):
                return error(429, "rate_limited", "Muitas mensagens em pouco tempo. Espere um minuto.", True, rid)
            if not daily_cap.take():
                return error(429, "daily_limit", "O atendimento de demonstração atingiu o limite de hoje.", False, rid)
            entry = CachedRequest(message=body.message, status="running")
            session.remember_request(rid, entry)
            generation = session.generation
            try:
                result = agent().run_turn(
                    message=body.message,
                    history=session.history(settings.history_turns),
                    known_products=session.known_products,
                    context_cents=session.shown_cents,
                    customer_id=session.customer_id,
                    context_lines=_context_lines(session, settings.timezone),
                )
            except ProviderUnavailable:
                session.requests.pop(rid, None)
                return error(503, "provider_unavailable",
                             "Não consegui consultar agora. Quer tentar de novo?", True, rid)
            except DeadlineExceeded:
                session.requests.pop(rid, None)
                return error(504, "deadline_exceeded", "A consulta demorou demais. Quer tentar de novo?", True, rid)
            if session.generation != generation:
                session.requests.pop(rid, None)
                return error(409, "session_changed", "O perfil mudou durante a resposta. Envie de novo.", True, rid)

            session.turns.append(result.contents)
            session.known_products.update(result.known_products)
            for card in result.cards:
                session.shown_cents |= {v for k, v in card.items() if k.endswith("_cents") and v}
            response = ChatResponse(
                request_id=body.request_id, text=result.text, cards=result.cards, sources=result.sources,
                next_action=result.next_action, handoff=result.handoff,
                trace=result.trace if settings.expose_trace else None,
            ).model_dump(mode="json", exclude_none=True)
            entry.status, entry.response = "done", response
            metrics.record(result.trace, result.cards, result.sources, result.handoff)
            return response
        finally:
            session.lock.release()

    # /admin (D20): the page is an empty shell (a browser navigation cannot send a header, and a token in the URL
    # would land in request logs); the numbers need X-Admin-Token. A wrong or missing token, or no token configured,
    # gets the same 404 body as a route that does not exist.
    @app.get("/admin")
    def admin_page():
        return FileResponse(STATIC / "admin.html", headers={"X-Robots-Tag": "noindex", "Cache-Control": "no-store"})

    @app.get("/admin/api/stats")
    def admin_stats(request: Request):
        token = request.headers.get("x-admin-token", "")
        if not settings.admin_token or not hmac.compare_digest(token.encode(), settings.admin_token.encode()):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return JSONResponse(metrics.snapshot(), headers={"Cache-Control": "no-store"})

    if STATIC.exists():
        app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


def _model_price(settings: Settings) -> tuple[str, dict | None, str | None]:
    """The served model's price from the one price file; a missing file or model means "cost unavailable", not 0."""
    try:
        pricing = json.loads(settings.pricing_path.read_text())
    except (OSError, ValueError):
        return settings.gemini_model, None, None
    return settings.gemini_model, pricing.get("models", {}).get(settings.gemini_model), pricing.get("checked_on")


WEEKDAYS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def _context_lines(session, timezone: str) -> list[str]:
    now = datetime.now(ZoneInfo(timezone))
    lines = [f"Now in Campo Grande: {now:%Y-%m-%d %H:%M} ({WEEKDAYS[now.weekday()]}). "
             "Holidays are not in the system; confirm special dates with the store."]
    if session.known_products:
        recent = list(session.known_products.items())[-5:]
        lines.append("Products already seen in this conversation (product_id: name): "
                     + "; ".join(f"{pid}: {name}" for pid, name in recent))
    lines.append("Customer profile: " + (session.profile_alias or "visitor (no profile selected)"))
    return lines


def get_app() -> FastAPI:
    """Uvicorn factory: `uvicorn app.main:get_app --factory`."""
    return create_app()
