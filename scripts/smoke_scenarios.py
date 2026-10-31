"""Order, hand-off and policy scenarios with the REAL Gemini API (costs tokens). Prints one JSON line per turn.

Scenarios: order 8 as a visitor (expects choose_profile), order 8 with profile demo-a (status, tracking and the
recorded estimate), shipping for exactly R$ 500 (expects a prepared hand-off) and an online return (expects the
missing delivery date to be asked).

Usage: .venv/bin/python scripts/smoke_scenarios.py gemini-3.1-flash-lite > evals/smoke/<date>-scenarios-<model>.jsonl
"""

from __future__ import annotations

import json
import sys
import uuid
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


def main() -> int:
    model = sys.argv[1] if len(sys.argv) > 1 else get_settings().gemini_model
    client = TestClient(create_app(replace(get_settings(), gemini_model=model)))

    def turn(message: str) -> None:
        r = client.post("/api/chat", json={"request_id": str(uuid.uuid4()), "message": message})
        body, trace = r.json(), r.json().get("trace", {})
        print(json.dumps({
            "model": model, "msg": message, "status": r.status_code, "text": body.get("text") or body.get("message"),
            "next": body.get("next_action"), "handoff": body.get("handoff"),
            "sources": [s["id"] for s in body.get("sources", [])],
            "tools": [(t["name"], t["args"]) for t in trace.get("tools", [])],
            "fallback": trace.get("text_fallback"), "corrected": trace.get("text_corrected"),
            "ms": trace.get("duration_ms"), "usage": trace.get("usage"),
        }, ensure_ascii=False))

    client.post("/api/session")
    turn("Onde está o meu pedido 8?")
    client.post("/api/session/profile", json={"profile": "demo-a"})
    turn("Onde está o meu pedido 8?")
    client.post("/api/session")
    turn("Quanto custa o frete de um pedido de exatamente R$ 500 na região metropolitana de Campo Grande?")
    client.post("/api/session")
    turn("Comprei online e me arrependi. Posso devolver?")
    return 0


if __name__ == "__main__":
    sys.exit(main())
