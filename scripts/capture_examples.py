"""Capture the five delivery conversations (guide 03 §6) on the deployed URL with real Gemini.

Writes, per conversation, examples/raw/NN-<slug>.json (everything the page received) and examples/NN-<slug>.md
(transcript in PT-BR with the English translation from examples/translations.json, cards, tools, sources,
timing, tokens, automatic checks and a screenshot). Missing translations are marked so they cannot ship silently.

Usage: .venv/bin/python scripts/capture_examples.py [--url https://...] [--only NN]
       .venv/bin/python scripts/capture_examples.py --rerender   # rebuild the .md files from raw/ (no API calls)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import expect, sync_playwright  # noqa: E402

from app.agent import _CLAIM_RE, _PROMISE_RE, money_mentions  # noqa: E402
from qa_capture import URL, Run, nylon_guitar_ids  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "examples"
PENDING = "TRANSLATION PENDING"
NYLON = nylon_guitar_ids()

# Each step is ("say", message) or ("profile", label prefix): the profile is chosen in the picker, then the last
# question is sent again, as a customer would.
CONVERSATIONS = [
    ("01", "discovery", "Discovery with a budget, then a follow-up on the chosen model", [
        ("say", "Tem violão de nylon até R$ 800?"),
        ("say", "Gostei do Yamaha C40. Quanto fica no PIX?"),
    ]),
    ("02", "promotion-pix", "Promotion and PIX do not stack", [
        ("say", "Quanto fica o Kalani KAL-700T no PIX?"),
    ]),
    ("03", "authorized-order", "Order 8: visitor first, then demo profile A", [
        ("say", "Onde está o meu pedido 8?"),
        ("profile", "Cliente A"),
    ]),
    ("04", "return-policy", "Return after an online purchase, with the missing fact asked and then given", [
        ("say", "Comprei online e me arrependi. Posso devolver?"),
        ("say", "Chegou anteontem, dia 29/10."),
    ]),
    ("05", "store-scope", "Out-of-scope item plus an instrument the store sells", [
        ("say", "Vocês vendem amplificador? Se não, podem me indicar um baixo?"),
    ]),
]


def checks(slug: str, turns: list[dict]) -> list[tuple[str, bool]]:
    """The facts each script must show (guide 03 §6), plus the D13 blockers on every turn."""
    out = []
    for i, t in enumerate(turns, 1):
        out.append((f"turn {i}: no claimed or promised action", not (_CLAIM_RE.search(t["text"]) or _PROMISE_RE.search(t["text"]))))
        out.append((f"turn {i}: not rewritten by the server fallback", not t["trace"].get("text_fallback")))
    last = turns[-1]
    if slug == "discovery":
        first = turns[0]
        out.append(("only available nylon guitars at or under R$ 800",
                    bool(first["cards"]) and all(c["product_id"] in NYLON and c["offer_cents"] <= 80000
                                                 and c["availability"] == "available" for c in first["cards"])))
        out.append(("Yamaha C40 on PIX = R$ 569,91 (product 81, 56991 cents)",
                    any(c["product_id"] == 81 and c.get("payment_cents") == 56991 for c in last["cards"])))
    elif slug == "promotion-pix":
        card = last["cards"][0] if last["cards"] else {}
        out.append(("card: product 127, list 35900, 10%, PIX 32310",
                    (card.get("product_id"), card.get("base_cents"), card.get("discount_percent"),
                     card.get("payment_cents")) == (127, 35900, 10, 32310)))
        out.append(("text states R$ 359,00, 10% and R$ 323,10 together; never R$ 306,95",
                    {35900, 32310} <= set(money_mentions(last["text"])) and "10%" in last["text"]
                    and "306,95" not in last["text"]))
    elif slug == "authorized-order":
        out.append(("visitor gets the profile picker and no order data",
                    turns[0]["next_action"] == "choose_profile" and "BRJL" not in turns[0]["text"]))
        out.append(("profile A gets status, tracking BRJL5544332BR and 'previsão registrada'",
                    "BRJL5544332BR" in last["text"] and "previsão registrada" in last["text"]))
    elif slug == "return-policy":
        first = turns[0]
        out.append(("first answer asks the missing fact (clarify) citing §4.1",
                    first["next_action"] == "clarify" and any(s["id"] == "4.1" for s in first["sources"])))
        # The UI lists sources per turn; a follow-up may rely on the §4.1 text retrieved in the previous turn.
        cited = {s["id"] for t in turns[-2:] for s in t["sources"]}
        out.append(("second answer applies §4.1 (retrieved in this or the previous turn) without asking the date again",
                    "4.1" in cited and "que dia" not in last["text"].lower()))
    elif slug == "store-scope":
        out.append(("says amplifiers are not sold and shows available basses from the catalog",
                    bool(last["cards"]) and all(c["availability"] == "available" for c in last["cards"])
                    and "query_catalog" in [x["name"] for x in last["trace"]["tools"]]))
    return out


def brl(cents):
    whole, frac = divmod(cents, 100)
    return f"R$ {whole:,}".replace(",", ".") + f",{frac:02d}"


def render(number, slug, title, meta, turns, results, translations) -> str:
    lines = [f"# {number} · {title}", "",
             "> Real conversation captured on the deployed demo (not a prepared example). Customer and agent text are "
             "in Brazilian Portuguese, as served; the English translation was written afterwards for the evaluators.",
             "",
             "| | |", "| --- | --- |",
             f"| URL | {meta['url']} |",
             f"| Revision / commit | `{meta['revision']}` / `{meta['commit']}` |",
             f"| Model | `{meta['model']}` |",
             f"| Dataset | `{meta['dataset_id']}` |",
             f"| Captured | {meta['captured']} (São Paulo) |",
             f"| Screenshot | [{Path(meta['screenshot']).name}]({meta['screenshot']}) |",
             "", "## Conversation", ""]
    for i, t in enumerate(turns, 1):
        if t.get("profile"):
            lines += [f"*The customer chose the demo profile **{t['profile']}** in the interface; the question was sent again.*", ""]
        en_q = translations.get(t["message"], PENDING)
        en_a = translations.get(t["text"], PENDING)
        lines += [f"**Turn {i} · Customer:** {t['message']}", f"<br>*EN:* {en_q}", "",
                  f"**Turn {i} · Empório:** {t['text']}", f"<br>*EN:* {en_a}", ""]
        if t["cards"]:
            lines.append("Cards shown:")
            for c in t["cards"]:
                price = brl(c["offer_cents"])
                if c.get("discount_percent"):
                    price = f"{brl(c['base_cents'])} −{c['discount_percent']}% → {price}"
                if c.get("payment_cents") and c.get("payment_method") not in (None, "table"):
                    price += f"; {c['payment_method']}: {brl(c['payment_cents'])}"
                lines.append(f"- `#{c['product_id']}` {c['name']} · {c['attribute']} · {price} · {c['availability']}")
            lines.append("")
        tools = ", ".join(f"`{x['name']}`" + (f" ({', '.join(f'{k}={v}' for k, v in x['args'].items() if k != 'sql')})"
                                              if x["args"] else "") for x in t["trace"]["tools"]) or "none"
        usage = t["trace"].get("usage", {})
        sources = "; ".join(s["label"] for s in t["sources"]) or "none"
        lines += [f"<sub>Tools: {tools} · sources: {sources} · next_action `{t['next_action']}` · "
                  f"{t['seconds']} s in the browser ({t['trace']['duration_ms']} ms server) · "
                  f"{t['trace']['model_calls']} model calls · tokens in/out {usage.get('input', 0)}/"
                  f"{usage.get('output', 0) + usage.get('thoughts', 0)}"
                  + (" · server asked the model to correct its text" if t["trace"].get("text_corrected") else "")
                  + "</sub>", ""]
        if t.get("handoff"):
            h = t["handoff"]
            lines += [f"Hand-off: `{h['delivery_status']}` ({h['reason']}) — {h['summary']}", ""]
    lines += ["## Automatic checks", "", "| Check | Result |", "| --- | --- |"]
    lines += [f"| {name} | {'pass' if ok else '**FAIL**'} |" for name, ok in results]
    lines += ["", "## Review", "", "See [the review of all five conversations](README.md).", ""]
    return "\n".join(lines)


def rerender() -> int:
    translations_path = OUT / "translations.json"
    translations = json.loads(translations_path.read_text()) if translations_path.exists() else {}
    pending = 0
    for number, slug, title, _ in CONVERSATIONS:
        raw = json.loads((OUT / "raw" / f"{number}-{slug}.json").read_text())
        results = checks(slug, raw["turns"])
        md = render(number, slug, title, raw["meta"], raw["turns"], results, translations)
        (OUT / f"{number}-{slug}.md").write_text(md)
        pending += md.count(PENDING)
        print(f"{number} {slug}: {'PASS' if all(ok for _, ok in results) else 'FAIL'}; translations pending: {md.count(PENDING)}")
    return 1 if pending else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=URL)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--rerender", action="store_true", help="rebuild markdown from raw/ with current translations")
    args = parser.parse_args()
    if args.rerender:
        return rerender()
    (OUT / "raw").mkdir(parents=True, exist_ok=True)
    (OUT / "screens").mkdir(parents=True, exist_ok=True)
    env = {**__import__("os").environ, "CLOUDSDK_ACTIVE_CONFIG_NAME": "emporio"}
    revision, commit = subprocess.run(
        ["gcloud", "run", "services", "describe", "emporio-agent", "--project", "emporio-da-musica-agent",
         "--region", "southamerica-east1", "--format=value(status.latestReadyRevisionName,metadata.labels.commit)"],
        capture_output=True, text=True, env=env).stdout.split()
    health = json.loads(subprocess.run(["curl", "-s", args.url + "/health"], capture_output=True, text=True).stdout)
    translations_path = OUT / "translations.json"
    translations = json.loads(translations_path.read_text()) if translations_path.exists() else {}
    failed = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        run = Run(browser, args.url)
        for number, slug, title, steps in CONVERSATIONS:
            if args.only and number not in args.only:
                continue
            page = run.page()
            turns, last_message = [], None
            for kind, value in steps:
                if kind == "say":
                    body, _ = run.ask(page, value)
                    turns.append({"message": value, **body, "seconds": body.pop("_seconds")})
                    last_message = value
                else:
                    page.locator(".picker").last.locator("button", has_text=value).click()
                    expect(page.locator("#profile-label")).to_contain_text(value)
                    body, _ = run.ask(page, last_message)
                    turns.append({"message": last_message, "profile": page.locator("#profile-label").inner_text(),
                                  **body, "seconds": body.pop("_seconds")})
            shot = f"screens/{number}-{slug}-390.png"
            page.screenshot(path=str(OUT / shot))
            page.context.close()
            meta = {"url": args.url, "revision": revision, "commit": commit, "model": health.get("model"),
                    "dataset_id": health.get("dataset_id"), "screenshot": shot,
                    "captured": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M")}
            results = checks(slug, turns)
            (OUT / "raw" / f"{number}-{slug}.json").write_text(
                json.dumps({"meta": meta, "turns": turns, "checks": results}, ensure_ascii=False, indent=2) + "\n")
            (OUT / f"{number}-{slug}.md").write_text(render(number, slug, title, meta, turns, results, translations))
            bad = [name for name, ok in results if not ok]
            print(f"{number} {slug}: {'PASS' if not bad else 'FAIL ' + str(bad)}")
            failed += bad
        browser.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
