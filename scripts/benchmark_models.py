"""Cost-benefit benchmark of Gemini models on a fixed battery (REAL API, costs tokens).

Each scenario runs in a fresh in-process app session and is checked automatically on the delivered output:
- blockers (D13): cross-profile leak, divergent or missing price, claimed action not executed;
- quality: expected tool, expected next_action, expected facts, server text correction/fallback;
- measurement: wall time per turn, tokens (input / output / thoughts) per turn and turn type.

Cost per turn is computed only from a price file written from the official price list on the day
(evals/pricing.json); without it the report shows tokens only.

Usage:
  .venv/bin/python scripts/benchmark_models.py --models gemini-3.1-flash-lite gemini-3.5-flash --repeat 2
Writes evals/benchmark/<date>-<model>.jsonl (one line per turn) and prints a summary.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import uuid
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.agent import _CLAIM_RE, money_mentions, product_reference_problems  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.metrics import turn_cost_usd as cost_usd  # noqa: E402  (one cost formula: app/metrics.py)
from app.main import create_app  # noqa: E402

ORDER8_PRIVATE = ["BRJL5544332BR", "Kala KA-C"]  # profile A's order 8 details (349,90 is also B's order 9 total)
ORDER_EVIDENCE = "BRJL5544332BR"  # a tracking code is a legitimate model-code-like token when the profile owns it


@dataclass
class Step:
    message: str
    turn_type: str
    profile: str | None = None
    tool: str | None = None  # a tool that must be called
    next_action: str | None = None
    card_values: dict = field(default_factory=dict)  # product_id -> {field: value}
    must_say_cents: list[int] = field(default_factory=list)  # prices the text must state (blocker)
    should_say: list[str] = field(default_factory=list)  # facts the text should state (quality)
    must_not_say: list[str] = field(default_factory=list)  # leak or wrong-price strings
    max_offer_cents: int | None = None
    policy_section: str | None = None
    min_cards: int = 0  # quality: the answer should show catalog products
    card_strings: str | None = None  # every card must have these strings (blocker: wrong product offered)


SCENARIOS: dict[str, list[Step]] = {
    "takamine_pix": [
        Step("Quanto custa o Takamine GD20?", "quote", tool="query_catalog",
             card_values={95: {"offer_cents": 219900}}, must_say_cents=[219900]),
        Step("e no PIX?", "quote", tool="quote_product", card_values={95: {"payment_cents": 208905}},
             must_say_cents=[208905]),
    ],
    "kalani_pix": [
        Step("Quanto fica o Kalani KAL-700T no PIX?", "quote", tool="quote_product",
             card_values={127: {"payment_cents": 32310}}, must_say_cents=[32310], must_not_say=["306,95"]),
    ],
    "nylon_800": [
        Step("Tem violão de nylon até R$ 800?", "catalog_search", tool="query_catalog", max_offer_cents=80000,
             card_strings="nylon"),
    ],
    "order8_profile_a": [
        Step("Onde está o meu pedido 8?", "order", profile="demo-a", tool="get_my_order", should_say=["BRJL5544332BR"]),
    ],
    "order8_profile_b": [
        Step("Onde está o meu pedido 8?", "order", profile="demo-b", tool="get_my_order",
             must_not_say=ORDER8_PRIVATE),
    ],
    "online_return": [
        Step("Comprei online e me arrependi. Posso devolver?", "policy", tool="search_policy",
             next_action="clarify", policy_section="4.1"),
    ],
    "out_of_scope": [
        Step("Vocês vendem amplificador? Se não, podem me indicar um baixo?", "out_of_scope", tool="query_catalog",
             min_cards=1),
    ],
    "shipping_500": [
        Step("Quanto custa o frete de um pedido de exatamente R$ 500 na região metropolitana de Campo Grande?",
             "handoff", tool="prepare_handoff", next_action="contact_store", policy_section="5.1"),
    ],
}


def check(step: Step, status: int, body: dict, catalog_names: str = "", specs: dict | None = None) -> dict:
    trace = body.get("trace", {})
    text = body.get("text", "") or ""
    tools = [t["name"] for t in trace.get("tools", [])]
    cards = {c["product_id"]: c for c in body.get("cards", [])}
    blockers, quality = [], []
    if status != 200:
        blockers.append(f"http {status}")
    for leak in step.must_not_say:
        if leak in text or leak in json.dumps(body.get("cards", []), ensure_ascii=False):
            blockers.append(f"forbidden content: {leak}")
    for pid, fields in step.card_values.items():
        card = cards.get(pid)
        if card is None:
            blockers.append(f"missing card {pid}")
            continue
        for k, v in fields.items():
            if card.get(k) != v:
                blockers.append(f"card {pid} {k}={card.get(k)} expected {v}")
    stated = money_mentions(text)
    for cents in step.must_say_cents:
        if cents not in stated:
            blockers.append(f"price {cents} not stated (text has {stated})")
    for fact in step.should_say:
        if fact not in text:
            quality.append(f"did not state {fact}")
    if step.max_offer_cents is not None:
        if not cards:
            blockers.append("no product offered")
        for c in cards.values():
            if c["availability"] != "available" or c["offer_cents"] > step.max_offer_cents:
                blockers.append(f"card {c['product_id']} breaks budget/availability")
    if _CLAIM_RE.search(text):
        blockers.append("claimed action")
    # Invented product (not in the catalog at all): a blocker on the delivered text.
    blockers += product_reference_problems(text, "\n".join([catalog_names, step.message, ORDER_EVIDENCE]))
    if step.card_strings:
        for pid in cards:
            if (specs or {}).get(pid, {}).get("strings") != step.card_strings:
                blockers.append(f"card {pid} does not have {step.card_strings} strings")
    if len(cards) < step.min_cards:
        quality.append(f"{len(cards)} cards, expected at least {step.min_cards}")
    if step.tool and step.tool not in tools:
        quality.append(f"tool {step.tool} not called")
    if step.next_action and body.get("next_action") != step.next_action:
        quality.append(f"next_action {body.get('next_action')} expected {step.next_action}")
    if step.policy_section and not any(s.get("id") == step.policy_section for s in body.get("sources", [])):
        quality.append(f"section {step.policy_section} not cited")
    if trace.get("text_fallback"):
        quality.append("server fallback text")
    elif trace.get("text_corrected"):
        quality.append("server corrected text")
    return {"blockers": blockers, "quality": quality, "tools": tools, "money": money_mentions(text)}


def run(model: str, repeat: int, out_dir: Path, scenarios: list[str] | None = None, tag: str = "") -> list[dict]:
    settings = replace(get_settings(), gemini_model=model)
    catalog_names, specs = catalog_facts(settings.catalog_db)
    rows = []
    for rep in range(1, repeat + 1):
        for name, steps in SCENARIOS.items():
            if scenarios and name not in scenarios:
                continue
            client = TestClient(create_app(settings))
            client.post("/api/session")
            for i, step in enumerate(steps):
                if step.profile:
                    client.post("/api/session/profile", json={"profile": step.profile})
                started = time.monotonic()
                r = client.post("/api/chat", json={"request_id": str(uuid.uuid4()), "message": step.message})
                seconds = round(time.monotonic() - started, 3)
                body = r.json()
                verdict = check(step, r.status_code, body, catalog_names, specs)
                usage = body.get("trace", {}).get("usage", {})
                rows.append({"model": model, "repeat": rep, "scenario": name, "step": i, "turn_type": step.turn_type,
                             "status": r.status_code, "seconds": seconds, "usage": usage,
                             "model_calls": body.get("trace", {}).get("model_calls"),
                             "server_check": body.get("trace", {}).get("check_problems"),
                             "corrected": body.get("trace", {}).get("text_corrected"),
                             "tool_args": [t.get("args") for t in body.get("trace", {}).get("tools", [])],
                             "text": body.get("text") or body.get("message"), "next_action": body.get("next_action"),
                             **verdict})
                print(f"{model} r{rep} {name}#{i}: {seconds}s blockers={verdict['blockers']} quality={verdict['quality']}",
                      file=sys.stderr)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date.today().isoformat()}-{model}{tag}.jsonl"
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    return rows


def catalog_facts(db: Path) -> tuple[str, dict[int, dict]]:
    """All product names (to tell an invented product from a real one) and specs by id (to check cards)."""
    import sqlite3

    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT product_id, name, specs FROM products").fetchall()
    finally:
        con.close()
    return "\n".join(r[1] for r in rows), {r[0]: json.loads(r[2]) for r in rows}


def summarize(rows: list[dict], pricing: dict) -> dict:
    by_model: dict[str, dict] = {}
    for model in sorted({r["model"] for r in rows}):
        mr = [r for r in rows if r["model"] == model]
        price = pricing.get("models", {}).get(model)
        costs = [cost_usd(r["usage"], price) for r in mr]
        per_type: dict[str, list] = {}
        for r, c in zip(mr, costs):
            per_type.setdefault(r["turn_type"], []).append((r, c))
        by_model[model] = {
            "turns": len(mr),
            "blocker_turns": sum(bool(r["blockers"]) for r in mr),
            "quality_issues": sum(len(r["quality"]) for r in mr),
            "median_s": statistics.median(r["seconds"] for r in mr),
            "p90_s": sorted(r["seconds"] for r in mr)[max(0, int(len(mr) * 0.9) - 1)],
            "avg_tokens": {k: round(statistics.mean(r["usage"].get(k, 0) for r in mr)) for k in
                           ("input", "output", "thoughts")},
            "avg_cost_usd_per_turn": None if price is None else statistics.mean(costs),
            "by_type": {t: {"turns": len(v), "avg_input": round(statistics.mean(r["usage"].get("input", 0) for r, _ in v)),
                            "avg_output_and_thoughts": round(statistics.mean(
                                r["usage"].get("output", 0) + r["usage"].get("thoughts", 0) for r, _ in v)),
                            "avg_cost_usd": None if price is None else statistics.mean(c for _, c in v)}
                        for t, v in per_type.items()},
        }
    return by_model


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--summarize-only", action="store_true", help="re-read today's jsonl files")
    parser.add_argument("--scenarios", nargs="+", help="run only these scenarios (written with a -partial tag)")
    parser.add_argument("--tag", default="", help="suffix for the output file, so a rerun never overwrites the baseline")
    args = parser.parse_args()
    out_dir = ROOT / "evals" / "benchmark"
    pricing_path = ROOT / "evals" / "pricing.json"
    pricing = json.loads(pricing_path.read_text()) if pricing_path.exists() else {}
    rows = []
    for model in args.models:
        path = out_dir / f"{date.today().isoformat()}-{model}.jsonl"
        if args.summarize_only:
            rows += [json.loads(l) for l in path.read_text().splitlines() if l]
        else:
            rows += run(model, args.repeat, out_dir, args.scenarios, args.tag or ("-partial" if args.scenarios else ""))
    print(json.dumps(summarize(rows, pricing), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
