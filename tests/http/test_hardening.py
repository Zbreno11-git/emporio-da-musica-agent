"""Hardening of the public demo (D21): headers, body limit, generic errors, closed docs, cookie flags."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.main import create_app
from tests.fakes import FakeLLM, say


def make_client(settings, script=()):
    client = TestClient(create_app(settings, llm=FakeLLM(list(script))))
    client.post("/api/session")
    return client


def test_security_headers(settings):
    client = make_client(settings)
    page = client.get("/")
    csp = page.headers["content-security-policy"]
    for directive in ("default-src 'self'", "script-src 'self'", "style-src 'self'", "frame-ancestors 'none'",
                      "base-uri 'none'", "object-src 'none'"):
        assert directive in csp
    assert "unsafe-inline" not in csp
    assert page.headers["x-content-type-options"] == "nosniff"
    assert page.headers["referrer-policy"] == "no-referrer"
    assert page.headers["x-frame-options"] == "DENY"
    api = client.get("/api/demo-profiles")
    assert api.headers["cache-control"] == "no-store"
    assert client.get("/static/app.js").headers["x-content-type-options"] == "nosniff"


def test_body_over_the_limit_is_413_with_or_without_length(settings):
    client = make_client(settings)
    big = b'{"request_id": "' + str(uuid.uuid4()).encode() + b'", "message": "' + b"a" * 20_000 + b'"}'
    r = client.post("/api/chat", content=big, headers={"content-type": "application/json"})
    assert r.status_code == 413 and r.json()["code"] == "payload_too_large"
    chunked = client.post("/api/chat", content=iter([big[:10_000], big[10_000:]]),
                          headers={"content-type": "application/json"})
    assert chunked.status_code == 413 and chunked.json()["code"] == "payload_too_large"


def test_unexpected_error_is_generic_and_releases_the_request_id(settings):
    client = make_client(settings, [RuntimeError("boom: internal detail /srv/app/agent.py"), say("Oi! Como posso ajudar?")])
    rid = str(uuid.uuid4())
    r = client.post("/api/chat", json={"request_id": rid, "message": "oi"})
    assert r.status_code == 500 and r.json()["code"] == "internal_error" and r.json()["retryable"] is True
    assert "boom" not in r.text and "Traceback" not in r.text and "/srv" not in r.text
    again = client.post("/api/chat", json={"request_id": rid, "message": "oi"})
    assert again.status_code == 200  # the failed attempt does not leave the id stuck "in progress"


def test_docs_and_schema_are_not_published(settings):
    client = make_client(settings)
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert client.get(path).status_code == 404


def test_session_cookie_flags(settings):
    client = TestClient(create_app(settings, llm=FakeLLM([])))
    behind_https = client.post("/api/session", headers={"x-forwarded-proto": "https"}).headers["set-cookie"].lower()
    assert "httponly" in behind_https and "samesite=lax" in behind_https and "secure" in behind_https
    local = client.post("/api/session").headers["set-cookie"].lower()
    assert "httponly" in local and "secure" not in local
