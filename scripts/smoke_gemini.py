"""Milestone-1 smoke test with the REAL Gemini API (costs tokens).

Runs, in one session, "Quanto custa o Takamine GD20?" and then "e no PIX?" through the HTTP app in-process and
checks the result against the reference values: card 95 at 219900 cents, then 208905 cents on PIX.
Prints a JSON summary (model, SDK version, durations, tokens, tools) to keep as evidence.

Usage: .venv/bin/python scripts/smoke_gemini.py --model gemini-3.5-flash
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402

TURNS = [
    ("Quanto custa o Takamine GD20?", {"product_id": 95, "offer_cents": 219900}),
    ("e no PIX?", {"product_id": 95, "payment_cents": 208905, "payment_method": "pix"}),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="overrides GEMINI_MODEL")
    args = parser.parse_args()
    settings = get_settings()
    if args.model:
        settings = replace(settings, gemini_model=args.model)
    client = TestClient(create_app(settings))
    client.post("/api/session")
    summary = {"model": settings.gemini_model, "google_genai": version("google-genai"), "turns": [], "passed": True}
    for message, expected in TURNS:
        started = time.monotonic()
        r = client.post("/api/chat", json={"request_id": str(uuid.uuid4()), "message": message})
        elapsed = round(time.monotonic() - started, 2)
        body = r.json()
        card = next((c for c in body.get("cards", []) if c["product_id"] == expected["product_id"]), None)
        ok = r.status_code == 200 and card is not None and all(card.get(k) == v for k, v in expected.items())
        summary["passed"] &= ok
        trace = body.get("trace", {})
        summary["turns"].append({
            "message": message, "status": r.status_code, "ok": ok, "seconds": elapsed,
            "text": body.get("text") or body.get("message"), "card": card,
            "tools": [(t["name"], t["args"]) for t in trace.get("tools", [])],
            "usage": trace.get("usage"), "model_calls": trace.get("model_calls"),
            "text_corrected": trace.get("text_corrected"), "text_fallback": trace.get("text_fallback"),
        })
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
