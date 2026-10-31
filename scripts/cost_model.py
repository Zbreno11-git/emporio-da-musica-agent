"""Monthly cost model for the store, from the measured benchmark turns (D19). Offline: no API calls.

Reads the benchmark turns (evals/benchmark/2026-10-31-<model>-s53.jsonl) and the official prices recorded in
evals/pricing.json (Gemini, Cloud Run and the USD→BRL rate, each with its source and date), and writes
evals/cost-model.md. The token cost formula is imported from app/metrics.py, the one the /admin page uses.

Usage:
  .venv/bin/python scripts/cost_model.py            # writes evals/cost-model.md and prints the summary
  .venv/bin/python scripts/cost_model.py --json     # prints the numbers as JSON (input for the PDF)
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.metrics import turn_cost_usd as cost_usd  # noqa: E402

BENCHMARK_DATE = "2026-10-31"
BENCHMARK_SUFFIX = "-s53"  # the rerun after the S5.3 guards: the agent that is delivered, not the first baseline
MODELS = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite"]  # pinned model and its documented replacement
VOLUMES = [500, 2_000, 10_000]  # conversations per month
TURNS_PER_CONVERSATION = 4  # stated assumption, not measured on real customers
SENSITIVITY_TURNS = [2, 8]
REQUESTS_PER_CONVERSATION_OVERHEAD = 10  # page, CSS, JS, fonts, avatar, session: every conversation loads once
OVERHEAD_SECONDS_PER_CONVERSATION = 1.0  # billable instance time for those static requests (upper bound)
TYPE_ORDER = ["quote", "catalog_search", "order", "policy", "handoff", "out_of_scope"]


def load_rows(model: str, bench_dir: Path) -> list[dict]:
    path = bench_dir / f"{BENCHMARK_DATE}-{model}{BENCHMARK_SUFFIX}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def turn_stats(rows: list[dict], price: dict) -> dict:
    costs = [cost_usd(r["usage"], price) for r in rows]
    by_type: dict[str, list[tuple[dict, float]]] = {}
    for r, c in zip(rows, costs):
        by_type.setdefault(r["turn_type"], []).append((r, c))
    return {
        "turns": len(rows),
        "mean_usd": statistics.mean(costs),
        "median_usd": statistics.median(costs),
        "max_usd": max(costs),
        "mean_model_calls": statistics.mean(r.get("model_calls") or 0 for r in rows),
        "mean_seconds": statistics.mean(r["seconds"] for r in rows),
        "by_type": {t: {"turns": len(v),
                        "avg_input": statistics.mean(r["usage"].get("input", 0) for r, _ in v),
                        "avg_output_and_thoughts": statistics.mean(
                            r["usage"].get("output", 0) + r["usage"].get("thoughts", 0) for r, _ in v),
                        "avg_usd": statistics.mean(c for _, c in v)}
                    for t, v in sorted(by_type.items(), key=lambda kv: TYPE_ORDER.index(kv[0]))},
    }


def history_growth_tokens(rows: list[dict]) -> int:
    """Extra input tokens per earlier turn kept in history, from the only measured pair (Takamine step 0 → 1)."""
    deltas = []
    for rep in sorted({r["repeat"] for r in rows}):
        steps = {r["step"]: r for r in rows if r["scenario"] == "takamine_pix" and r["repeat"] == rep}
        if 0 in steps and 1 in steps:
            deltas.append(steps[1]["usage"]["input"] - steps[0]["usage"]["input"])
    return round(statistics.mean(deltas)) if deltas else 0


def gemini_monthly(mean_usd_per_turn: float, conversations: int, turns: int) -> float:
    return mean_usd_per_turn * turns * conversations


def history_extra_per_turn(growth_tokens: int, turns: int, price: dict) -> float:
    """Turn k carries (k-1) earlier turns; the mean over a conversation is (turns-1)/2 of them."""
    return growth_tokens * (turns - 1) / 2 * price["input_per_mtok"] / 1_000_000


def cloud_run_monthly(conversations: int, turns: int, seconds_per_turn: float, cr: dict) -> dict:
    """Request-based billing upper bound: every turn bills its full latency, as if no request ever overlapped."""
    shape, free = cr["service_shape"], cr["free_tier_monthly"]
    seconds = conversations * (turns * seconds_per_turn + OVERHEAD_SECONDS_PER_CONVERSATION)
    vcpu_s, gib_s = seconds * shape["vcpu"], seconds * shape["memory_gib"]
    requests = conversations * (turns + REQUESTS_PER_CONVERSATION_OVERHEAD)
    gross = (vcpu_s * cr["vcpu_second_usd"] + gib_s * cr["gib_second_usd"]
             + requests * cr["requests_per_million_usd"] / 1_000_000)
    discount = (min(vcpu_s, free["vcpu_seconds"]) * free["tier1_vcpu_second_usd"]
                + min(gib_s, free["gib_seconds"]) * free["tier1_gib_second_usd"]
                + min(requests, free["requests"]) * cr["requests_per_million_usd"] / 1_000_000)
    return {"vcpu_seconds": vcpu_s, "gib_seconds": gib_s, "requests": requests,
            "gross_usd": gross, "net_of_free_tier_usd": max(0.0, gross - discount)}


def build(pricing: dict, bench_dir: Path) -> dict:
    out = {"models": {}, "assumptions": {
        "turns_per_conversation": TURNS_PER_CONVERSATION, "volumes": VOLUMES,
        "requests_overhead_per_conversation": REQUESTS_PER_CONVERSATION_OVERHEAD,
        "overhead_seconds_per_conversation": OVERHEAD_SECONDS_PER_CONVERSATION}}
    for model in MODELS:
        price = pricing["models"][model]
        rows = load_rows(model, bench_dir)
        stats = turn_stats(rows, price)
        growth = history_growth_tokens(rows)
        worst_type = max(stats["by_type"].values(), key=lambda t: t["avg_usd"])["avg_usd"]
        projection = []
        for volume in VOLUMES:
            row = {"conversations": volume,
                   "gemini_usd": gemini_monthly(stats["mean_usd"], volume, TURNS_PER_CONVERSATION),
                   "cloud_run": cloud_run_monthly(volume, TURNS_PER_CONVERSATION, stats["mean_seconds"],
                                                  pricing["cloud_run"])}
            for turns in SENSITIVITY_TURNS:
                row[f"gemini_usd_{turns}_turns"] = gemini_monthly(stats["mean_usd"], volume, turns)
                row[f"gemini_usd_{turns}_turns_with_history"] = gemini_monthly(
                    stats["mean_usd"] + history_extra_per_turn(growth, turns, price), volume, turns)
            row["gemini_usd_worst_type"] = gemini_monthly(worst_type, volume, TURNS_PER_CONVERSATION)
            projection.append(row)
        out["models"][model] = {"price": price, "stats": stats, "history_growth_tokens": growth,
                                "worst_type_usd": worst_type, "projection": projection}
    return out


def usd(v: float, digits: int = 2) -> str:
    return f"US$ {v:,.{digits}f}"


def brl(v_usd: float, rate: float) -> str:
    whole, cents = f"{v_usd * rate:,.2f}".split(".")
    return f"R$ {whole.replace(',', '.')},{cents}"


def render(model_data: dict, pricing: dict) -> str:
    fx, cr = pricing["fx"], pricing["cloud_run"]
    rate = fx["usd_brl"]
    pinned, alt = MODELS
    p = model_data["models"][pinned]
    lines = [
        "# Cost model (D19)",
        "",
        "> Generated by [`scripts/cost_model.py`](../scripts/cost_model.py) from the measured benchmark turns of "
        f"{BENCHMARK_DATE} after the S5.3 guards (files `*{BENCHMARK_SUFFIX}.jsonl` in [`benchmark/`](benchmark/), "
        "the agent as delivered) and the official prices in [`pricing.json`](pricing.json). "
        "Do not edit by hand; rerun the script.",
        "",
        "**Sources.**",
        f"- Gemini prices: {pricing['source']}, checked on {pricing['checked_on']} ({pricing['unit']}).",
        f"- Cloud Run prices: {cr['source']}, checked on {cr['checked_on']}.",
        f"- Exchange rate: US$ 1 = R$ {rate:.4f} ({fx['kind']} of {fx['date']}, Banco Central do Brasil).",
        "",
        "## 1. Cost per answer",
        "",
        "One answer is one customer turn: every model call, tool round and server-side text correction in it.",
        "",
        "| Model | Turns measured | Mean | Median | Max | Model calls per turn | Mean turn latency |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for model in MODELS:
        s = model_data["models"][model]["stats"]
        lines.append(f"| `{model}` | {s['turns']} | {usd(s['mean_usd'], 5)} | {usd(s['median_usd'], 5)} | "
                     f"{usd(s['max_usd'], 5)} | {s['mean_model_calls']:.2f} | {s['mean_seconds']:.2f} s |")
    lines += [
        "",
        f"On the pinned model, **1,000 answers cost about {usd(p['stats']['mean_usd'] * 1000)} "
        f"({brl(p['stats']['mean_usd'] * 1000, rate)})**.",
        "",
        "## 2. Cost per turn type",
        "",
        "| Turn type | Model | Turns | Avg input tokens | Avg output + thinking tokens | Avg cost per turn |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for t in TYPE_ORDER:
        for model in MODELS:
            bt = model_data["models"][model]["stats"]["by_type"].get(t)
            if bt:
                lines.append(f"| {t.replace('_', ' ')} | `{model}` | {bt['turns']} | {bt['avg_input']:,.0f} | "
                             f"{bt['avg_output_and_thoughts']:,.0f} | {usd(bt['avg_usd'], 5)} |")
    lines += [
        "",
        "Input dominates. Every model call carries the system prompt and the five tool schemas: the out-of-scope "
        f"turns, a single call with no tool, used {p['stats']['by_type']['out_of_scope']['avg_input']:,.0f} input "
        "tokens. A turn that uses a tool makes two or three calls, and each one resends that prefix plus the tool "
        "results.",
        "",
        "## 3. Monthly projection for the store",
        "",
        f"**Assumption:** {TURNS_PER_CONVERSATION} customer turns per conversation (not measured on real customers). "
        "Gemini = mean cost per turn × turns × conversations.",
        "",
        "| Conversations / month | Gemini (`" + pinned + "`) | Cloud Run, gross (upper bound) | "
        "Cloud Run after the free tier | Total | Total (BRL) |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in p["projection"]:
        c = row["cloud_run"]
        total = row["gemini_usd"] + c["gross_usd"]
        lines.append(f"| {row['conversations']:,} | {usd(row['gemini_usd'])} | {usd(c['gross_usd'])} | "
                     f"{usd(c['net_of_free_tier_usd'])} | {usd(total)} | {brl(total, rate)} |")
    lines += [
        "",
        "Total uses Cloud Run **gross** (no free tier), the conservative figure.",
        f"Arithmetic check: {usd(p['stats']['mean_usd'], 6)} × {TURNS_PER_CONVERSATION} × 2,000 = "
        f"{usd(p['stats']['mean_usd'] * TURNS_PER_CONVERSATION * 2000)}.",
        "",
        "**Cloud Run line.** Request-based billing in `southamerica-east1` (Tier 2): "
        f"US$ {cr['vcpu_second_usd']:.7f} per vCPU-second, US$ {cr['gib_second_usd']:.7f} per GiB-second and "
        f"US$ {cr['requests_per_million_usd']:.2f} per million requests, with the deployed shape "
        f"({cr['service_shape']['vcpu']} vCPU, {cr['service_shape']['memory_gib']} GiB, min instances 0).",
        f"- Billable time per conversation = turns × mean turn latency ({p['stats']['mean_seconds']:.2f} s) + "
        f"{OVERHEAD_SECONDS_PER_CONVERSATION:.0f} s for the page load.",
        f"- Requests = turns + {REQUESTS_PER_CONVERSATION_OVERHEAD} static/session requests.",
        "- This is an **upper bound**: with concurrency 20, overlapping requests share billed instance time.",
        "- The free tier (180,000 vCPU-s, 360,000 GiB-s and 2 million requests a month) belongs to the billing "
        "account and is shared with its other projects, so the gross figure is the safe one to budget.",
        "",
        "## 4. Sensitivity",
        "",
        f"| Conversations / month | {TURNS_PER_CONVERSATION} turns (base) | 2 turns | 8 turns | "
        "8 turns with history growth | Every turn at the most expensive type |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in p["projection"]:
        lines.append(f"| {row['conversations']:,} | {usd(row['gemini_usd'])} | {usd(row['gemini_usd_2_turns'])} | "
                     f"{usd(row['gemini_usd_8_turns'])} | {usd(row['gemini_usd_8_turns_with_history'])} | "
                     f"{usd(row['gemini_usd_worst_type'])} |")
    lines += [
        "",
        f"- **History growth:** each earlier turn kept in history added about {p['history_growth_tokens']:,} input "
        "tokens to the next turn (Takamine step 0 → 1, the only multi-turn pair measured). History is capped at "
        "10 turns. The benchmark's mean already includes that pair, so this column slightly double-counts.",
        f"- **Most expensive type:** {usd(p['worst_type_usd'], 5)} per turn on the pinned model.",
        "",
        "## 5. Model lines",
        "",
        "| Conversations / month | `" + pinned + "` (pinned) | `" + alt + "` (replacement) |",
        "| --- | --- | --- |",
    ]
    for row_p, row_a in zip(p["projection"], model_data["models"][alt]["projection"]):
        lines.append(f"| {row_p['conversations']:,} | {usd(row_p['gemini_usd'])} | {usd(row_a['gemini_usd'])} |")
    lines += [
        "",
        f"- `{pinned}` shuts down on 2027-05-07; Google's recommended replacement `{alt}` passed every blocker in "
        "the benchmark at the cost shown.",
        "- `gemini-3.6-flash` (no quality notes, about 5× the cost per turn, 3.6× the median latency) doubles its "
        "price on 2027-01-01; it is not projected here.",
        "",
        "## 6. Caveats",
        "",
        "- 18 measured turns per model; the turn-type mix is the benchmark's, not the store's real traffic.",
        "- Turns per conversation is an assumption; the sensitivity table shows how the cost moves with it.",
        "- Prices are the list prices on the dates above; billing in BRL follows Google's SKU prices in BRL, which "
        "may differ slightly from the PTAX conversion.",
        "- Excluded: Secret Manager and Artifact Registry storage (cents per month at this scale), "
        "network egress (small JSON and static files), and taxes.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print the numbers as JSON instead of writing markdown")
    args = parser.parse_args()
    pricing = json.loads((ROOT / "evals" / "pricing.json").read_text())
    data = build(pricing, ROOT / "evals" / "benchmark")
    if args.json:
        print(json.dumps(data, indent=2))
        return 0
    (ROOT / "evals" / "cost-model.md").write_text(render(data, pricing))
    for model in MODELS:
        s = data["models"][model]["stats"]
        mid = data["models"][model]["projection"][1]
        print(f"{model}: mean {s['mean_usd']:.5f} USD/turn · 2,000 conversations × {TURNS_PER_CONVERSATION} turns "
              f"→ Gemini {mid['gemini_usd']:.2f} USD/month, Cloud Run gross {mid['cloud_run']['gross_usd']:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
