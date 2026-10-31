"""Hosted QA run (D21): clicks the customer flows on the deployed URL with real Gemini and records what it saw.

Each case drives the real page in Chromium (Campo Grande time zone), reads the API response the page received, checks
the expected facts automatically and saves a screenshot. Output:
- docs/qa/screens/NN-<case>-<width>.png
- docs/qa/hosted-results.md (generated table: case, expected, observed, verdict, screenshot)
Costs about 15 Gemini turns (≈ US$ 0.03). The /admin case reads ADMIN_TOKEN from the local .env (never printed).

Usage: .venv/bin/python scripts/qa_capture.py [--url https://...]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = "https://emporio-agent-669786539213.southamerica-east1.run.app"
SCREENS = ROOT / "docs" / "qa" / "screens"
AGENT = ".turn-agent:not(.typing-turn)"
NBSP = " "


def nylon_guitar_ids() -> set[int]:
    """Acoustic guitars (category 5) with nylon strings, read from the same catalog the server uses."""
    import sqlite3

    con = sqlite3.connect(f"file:{ROOT / 'data' / 'build' / 'catalog.db'}?mode=ro", uri=True)
    try:
        return {r[0] for r in con.execute("SELECT product_id FROM products WHERE category_id = 5 "
                                          "AND json_extract(specs, '$.strings') = 'nylon'")}
    finally:
        con.close()


class Run:
    def __init__(self, browser, base):
        self.browser, self.base, self.rows = browser, base, []

    def page(self, width=390, height=844):
        ctx = self.browser.new_context(viewport={"width": width, "height": height}, locale="pt-BR",
                                       timezone_id="America/Campo_Grande", reduced_motion="reduce")
        page = ctx.new_page()
        page.errors = []
        page.on("console", lambda m: page.errors.append(m.text) if m.type == "error" else None)
        page.goto(self.base + "/")
        return page

    def ask(self, page, text):
        before = page.locator(AGENT).count()
        page.fill("#message", text)
        started = time.monotonic()
        with page.expect_response("**/api/chat", timeout=40000) as resp:
            page.click("#send")
        expect(page.locator(AGENT)).to_have_count(before + 1, timeout=40000)
        body = resp.value.json()
        body["_seconds"] = round(time.monotonic() - started, 2)
        return body, page.locator(AGENT).nth(before)

    def record(self, case, title, expected, observed, ok, page, width=390):
        shot = f"{len(self.rows) + 1:02d}-{case}-{width}.png"
        page.screenshot(path=str(SCREENS / shot))
        ok = ok and not page.errors
        if page.errors:
            observed += f"; console errors: {page.errors}"
        self.rows.append({"case": case, "title": title, "expected": expected, "observed": observed,
                          "verdict": "pass" if ok else "FAIL", "screenshot": f"screens/{shot}"})
        print(f"{'PASS' if ok else 'FAIL'} {case} ({width}): {observed}", file=sys.stderr)


def money(text):
    return text.replace(NBSP, " ")


def cards(body, key="offer_cents"):
    return [(c["product_id"], c.get(key)) for c in body["cards"]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=URL)
    args = parser.parse_args()
    SCREENS.mkdir(parents=True, exist_ok=True)
    revision = subprocess.run(
        ["gcloud", "run", "services", "describe", "emporio-agent", "--project", "emporio-da-musica-agent",
         "--region", "southamerica-east1", "--format=value(status.latestReadyRevisionName,metadata.labels.commit)"],
        capture_output=True, text=True, env={**__import__("os").environ, "CLOUDSDK_ACTIVE_CONFIG_NAME": "emporio"},
    ).stdout.split()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        run = Run(browser, args.url)

        for width, height in [(390, 844), (320, 640), (1280, 860)]:
            page = run.page(width, height)
            b1, t1 = run.ask(page, "Quanto custa o Takamine GD20?")
            b2, t2 = run.ask(page, "e no PIX?")
            p1, p2 = money(t1.locator(".price").first.inner_text()), money(t2.locator(".price").first.inner_text())
            overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
            ok = (cards(b1)[:1] == [(95, 219900)] and cards(b2, "payment_cents")[:1] == [(95, 208905)]
                  and p1 == "R$ 2.199,00" and p2 == "R$ 2.089,05" and overflow <= 0)
            run.record("takamine-pix", "Price, then \"e no PIX?\" in the same conversation",
                       "Card R$ 2.199,00 (219900), then R$ 2.089,05 (208905) on PIX for product 95; no horizontal scroll",
                       f"cards {cards(b1)} → {cards(b2, 'payment_cents')}; card text {p1} → {p2}; overflow {overflow}px; "
                       f"{b1['_seconds']} s / {b2['_seconds']} s", ok, page, width)
            page.context.close()

        page = run.page()
        b, t = run.ask(page, "Tem violão de nylon até R$ 800?")
        ids = [c["product_id"] for c in b["cards"]]
        nylon = nylon_guitar_ids()
        ok = bool(ids) and all(i in nylon and c["offer_cents"] <= 80000 and c["availability"] == "available"
                               for i, c in zip(ids, b["cards"]))
        run.record("discovery", "Open search with budget and string type",
                   "Only available nylon guitars at or under R$ 800, introduced by a sentence",
                   f"cards {cards(b)}; text: {b['text'][:140]}", ok, page)
        page.context.close()

        page = run.page()
        b, t = run.ask(page, "Quanto fica o Kalani KAL-700T no PIX?")
        card = b["cards"][0] if b["cards"] else {}
        ok = card.get("product_id") == 127 and card.get("payment_cents") == 32310 and "306,95" not in b["text"]
        run.record("promo-pix", "Promotion and PIX do not stack (manual §6.2)",
                   "R$ 323,10 on PIX (promotional price kept, no extra 5%); never R$ 306,95",
                   f"card {card.get('product_id')} payment {card.get('payment_cents')} list {card.get('base_cents')} "
                   f"-{card.get('discount_percent')}%; text: {b['text'][:140]}", ok, page)
        page.context.close()

        page = run.page()
        b, t = run.ask(page, "Onde está o meu pedido 8?")
        expect(t.locator(".picker-options button")).to_have_count(3, timeout=15000)
        run.record("order-visitor", "Order question without a profile",
                   "next_action choose_profile and the demo-profile picker; no order data",
                   f"next_action {b['next_action']}; text: {b['text'][:120]}",
                   b["next_action"] == "choose_profile" and "BRJL" not in b["text"], page)
        t.locator(".picker-options button", has_text="Cliente B").click()
        expect(page.locator("#profile-label")).to_have_text("Cliente B · pedido confirmado")
        b, t = run.ask(page, "Onde está o meu pedido 8?")
        leak = any(s in json.dumps(b, ensure_ascii=False) for s in ("BRJL5544332BR", "Kala KA-C"))
        run.record("order-profile-b", "Another profile's order",
                   "Same answer as a non-existent order: no status, item or tracking of order 8",
                   f"leak={leak}; text: {b['text'][:140]}", not leak, page)
        page.click("#change-profile")
        expect(page.locator(".picker")).to_have_count(2)
        page.locator(".picker").last.locator("button", has_text="Cliente A").click()
        expect(page.locator("#profile-label")).to_have_text("Cliente A · pedido em transporte")
        b, t = run.ask(page, "Onde está o meu pedido 8?")
        ok = "BRJL5544332BR" in b["text"] and "previsão registrada" in b["text"]
        run.record("order-profile-a", "The owner's order",
                   "Status, item, tracking BRJL5544332BR and the estimate called \"a previsão registrada\"",
                   f"text: {b['text'][:200]}", ok, page)
        page.context.close()

        page = run.page()
        b, t = run.ask(page, "Comprei online e me arrependi. Posso devolver?")
        cited = [s["id"] for s in b["sources"] if s["type"] == "policy"]
        ok = b["next_action"] == "clarify" and "4.1" in cited
        run.record("return", "Return with a missing fact",
                   "States the online rule (§4.1) and asks the one missing fact (the delivery date)",
                   f"next_action {b['next_action']}; sources {cited}; text: {b['text'][:160]}", ok, page)
        page.context.close()

        page = run.page()
        b, t = run.ask(page, "Vocês vendem amplificador? Se não, podem me indicar um baixo?")
        ok = bool(b["cards"]) and all(c["availability"] == "available" for c in b["cards"]) and \
            "query_catalog" in [x["name"] for x in b["trace"]["tools"]]
        run.record("out-of-scope", "Out-of-scope item plus an in-scope request",
                   "Says the store does not sell amplifiers and shows available basses from the catalog",
                   f"cards {cards(b)}; text: {b['text'][:140]}", ok, page)
        page.context.close()

        page = run.page()
        b, t = run.ask(page, "Quanto custa o frete de um pedido de exatamente R$ 500 na região metropolitana de Campo Grande?")
        ok = b["next_action"] == "contact_store" and (b.get("handoff") or {}).get("delivery_status") == "prepared"
        if ok:
            expect(t.locator(".handoff")).to_contain_text("Ainda não foi enviado")
        run.record("handoff", "Manual gap (shipping for exactly R$ 500, §5.1)",
                   "Explains the known part and prepares a hand-off marked as not sent",
                   f"next_action {b['next_action']}; handoff {(b.get('handoff') or {}).get('delivery_status')}; "
                   f"text: {b['text'][:140]}", ok, page)
        page.context.close()

        token = next((l.split("=", 1)[1] for l in (ROOT / ".env").read_text().splitlines()
                      if l.startswith("ADMIN_TOKEN=")), "")
        page = run.page(1280, 900)
        page.goto(args.url + "/admin")
        page.fill("#token", token)
        page.get_by_role("button", name="Ver números").click()
        expect(page.locator("#stats")).to_be_visible()
        turns = int(page.locator("#turns").inner_text())
        topics = page.locator("#topics tbody tr").count()
        products = page.locator("#products li").count()
        run.record("admin", "Store panel after this run",
                   "Average cost per answer, topics and top 3 products; no customer text",
                   f"answers {turns}; average {money(page.locator('#avg').inner_text())}; topics {topics}; "
                   f"products listed {products}", turns > 0 and products == 3, page, 1280)
        browser.close()

    when = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Hosted QA run (generated)",
        "",
        f"> Generated by [`scripts/qa_capture.py`](../../scripts/qa_capture.py) on {when} (São Paulo) against "
        f"{args.url}, revision `{' / commit '.join(revision) if revision else 'unknown'}`, real Gemini. Do not edit by hand.",
        "",
        "| # | Case | Expected | Observed | Verdict | Screenshot |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for i, r in enumerate(run.rows, 1):
        observed = re.sub(r"\s+", " ", r["observed"]).replace("|", "/")
        lines.append(f"| {i} | {r['title']} | {r['expected']} | {observed} | {r['verdict']} | "
                     f"[{Path(r['screenshot']).name}]({r['screenshot']}) |")
    (ROOT / "docs" / "qa" / "hosted-results.md").write_text("\n".join(lines) + "\n")
    failed = [r["case"] for r in run.rows if r["verdict"] != "pass"]
    print(f"{len(run.rows) - len(failed)}/{len(run.rows)} hosted cases passed {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
