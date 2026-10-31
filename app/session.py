"""In-memory sessions (guide 02 §7): opaque id, idle TTL, per-session lock, request dedup and rate limit.

Scope: one process. A restart or a new Cloud Run instance loses sessions; the API answers 410 and the UI
creates a new session. A profile switch bumps `generation`, so a turn that started under the previous
profile is discarded instead of being written to the new context.
"""

from __future__ import annotations

import secrets
import threading
import time
from collections import OrderedDict, deque
from dataclasses import dataclass, field

from google.genai import types

MAX_REQUEST_IDS = 20


@dataclass
class CachedRequest:
    message: str
    status: str  # "running" | "done"
    response: dict | None = None


@dataclass
class Session:
    id: str
    created: float
    last_seen: float
    profile_alias: str | None = None
    customer_id: int | None = None
    generation: int = 0
    turns: list[list[types.Content]] = field(default_factory=list)
    known_products: dict[int, str] = field(default_factory=dict)
    shown_cents: set[int] = field(default_factory=set)
    requests: "OrderedDict[str, CachedRequest]" = field(default_factory=OrderedDict)
    recent_turns: deque = field(default_factory=deque)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def history(self, max_turns: int) -> list[types.Content]:
        return [c for turn in self.turns[-max_turns:] for c in turn]

    def reset_context(self) -> None:
        self.generation += 1
        self.turns.clear()
        self.known_products.clear()
        self.shown_cents.clear()
        self.requests.clear()

    def remember_request(self, request_id: str, entry: CachedRequest) -> None:
        self.requests[request_id] = entry
        self.requests.move_to_end(request_id)
        while len(self.requests) > MAX_REQUEST_IDS:
            self.requests.popitem(last=False)

    def allow_turn(self, per_minute: int, now: float) -> bool:
        while self.recent_turns and now - self.recent_turns[0] > 60:
            self.recent_turns.popleft()
        if len(self.recent_turns) >= per_minute:
            return False
        self.recent_turns.append(now)
        return True


class DailyTurnCap:
    """Process-wide cap on model turns per UTC day. It fails loudly (429) instead of silently spending more."""

    def __init__(self, limit: int, today=lambda: time.strftime("%Y-%m-%d", time.gmtime())):
        self.limit, self.today = limit, today
        self.day, self.count = today(), 0
        self._lock = threading.Lock()

    def take(self) -> bool:
        with self._lock:
            if self.today() != self.day:
                self.day, self.count = self.today(), 0
            if self.count >= self.limit:
                return False
            self.count += 1
            return True


class SessionStore:
    def __init__(self, ttl_s: int, max_sessions: int, clock=time.monotonic):
        self.ttl_s = ttl_s
        self.max_sessions = max_sessions
        self.clock = clock
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self) -> Session | None:
        now = self.clock()
        with self._lock:
            self._sweep(now)
            if len(self._sessions) >= self.max_sessions:
                return None
            sid = secrets.token_urlsafe(32)
            session = Session(id=sid, created=now, last_seen=now)
            self._sessions[sid] = session
            return session

    def get(self, sid: str | None) -> Session | None:
        if not sid:
            return None
        now = self.clock()
        with self._lock:
            session = self._sessions.get(sid)
            if session is None:
                return None
            if now - session.last_seen > self.ttl_s:
                del self._sessions[sid]
                return None
            session.last_seen = now
            return session

    def rotate(self, session: Session) -> str:
        """Give the session a new id (after an identity change) and invalidate the old one."""
        with self._lock:
            self._sessions.pop(session.id, None)
            session.id = secrets.token_urlsafe(32)
            self._sessions[session.id] = session
            return session.id

    def delete(self, sid: str | None) -> None:
        with self._lock:
            self._sessions.pop(sid or "", None)

    def _sweep(self, now: float) -> None:
        for sid in [k for k, v in self._sessions.items() if now - v.last_seen > self.ttl_s]:
            del self._sessions[sid]
