"""Curated mutation net: each mutation is a real defect that one specific test must catch.

For each item: apply the change to the file, run only the expected test and restore the original.
A mutation that "escapes" (the test stays green) proves the test does not protect that rule.
Usage: .venv/bin/python scripts/mutation_check.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
Q, I, C = "app/tools/quote.py", "scripts/import_snapshot.py", "app/tools/catalog.py"
TQ, TI, TC = "tests/domain/test_quote.py", "tests/domain/test_import_snapshot.py", "tests/tools/test_catalog_sql.py"
A, M, S = "app/agent.py", "app/main.py", "app/session.py"
TH = "tests/http/test_chat_api.py"
TPM = "tests/domain/test_product_mentions.py"
FJ, TJ = "app/static/format.js", "tests/js/test_node_units.py::test_format_rules"
O, P, TO, TP = "app/tools/orders.py", "app/tools/policies.py", "tests/tools/test_orders.py", "tests/tools/test_policies.py"
B, CM, TCM = "scripts/benchmark_models.py", "scripts/cost_model.py", "tests/evals/test_cost_model.py"

MUTATIONS = [
    # (file, original snippet, defect, test that must fail)
    (Q, "    pix = offer if promotion_percent else _percent_of(base_cents, 100 - PIX_DISCOUNT_PERCENT)",
     "    pix = _percent_of(offer, 100 - PIX_DISCOUNT_PERCENT)", f"{TQ}::test_pix_is_not_applied_over_promotion"),
    (Q, "MID_MIN_INSTALLMENT_CENTS = 8_000", "MID_MIN_INSTALLMENT_CENTS = 10_000", f"{TQ}::test_installment_rules"),
    (Q, '    if avail != "available":', '    if avail == "discontinued":',
     f"{TQ}::test_unavailable_products_get_no_offer"),
    (Q, '    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))',
     "    return int(float(amount) * 100)", f"{TQ}::test_to_cents_uses_decimal_from_text"),
    (I, "        if k in seen:", "        if False:", f"{TI}::test_invalid_rows_abort_with_line_and_reason"),
    (I, "            if product_id in active_promo:", "            if False:",
     f"{TI}::test_invalid_rows_abort_with_line_and_reason"),
    (I, "        staging.rename(out)\n", "        staging.rename(out)\n        raise SnapshotError('x')\n",
     f"{TI}::test_failed_import_preserves_previous_build"),
    (I, '    demo_orders = [o for o in data["orders"] if o["customer_id"] in demo_ids]',
     '    demo_orders = list(data["orders"])',
     f"{TI}::test_orders_db_has_no_personal_columns_and_only_demo_customers"),
    (C, "    return sqlite3.SQLITE_DENY  # includes", "    return sqlite3.SQLITE_OK  # includes",
     f"{TC}::test_violations_are_blocked"),
    (C, '        return sqlite3.SQLITE_OK if (arg2 or "").lower() in ALLOWED_FUNCTIONS else sqlite3.SQLITE_DENY',
     "        return sqlite3.SQLITE_OK", f"{TC}::test_violations_are_blocked"),
    (C, '        if allowed is not None and (arg2 in allowed or arg2 == ""):', "        if True:",
     f"{TC}::test_violations_are_blocked"),
    (C, "    con.set_progress_handler(progress, VM_STEP_INTERVAL)", "    pass",
     f"{TC}::test_expensive_valid_query_is_interrupted"),
    (C, "        rows = cur.fetchmany(MAX_ROWS_READ)", "        rows = cur.fetchall()",
     f"{TC}::test_rows_read_are_capped_without_limit"),
    (C, '        sellable = [p for p in products if p["availability"] == "available"]',
     "        sellable = list(products)",
     f"{TC}::test_discover_drops_unavailable_and_over_budget_even_if_sql_forgets"),
    (C, '            within = [p for p in products if (p["pix_cents"] if on_pix else p["offer_cents"]) <= cap]',
     "            within = list(products)",
     f"{TC}::test_discover_drops_unavailable_and_over_budget_even_if_sql_forgets"),
    (A, "    problems += [f\"claims an action that was not executed: '{m.group(0)}'\" for m in _CLAIM_RE.finditer(text)]",
     "    pass", f"{TH}::test_claimed_action_is_rejected"),
    (A, '    problems = [f"amount {brl(v)} has no evidence" for v in money_mentions(text) if v not in cents]',
     "    problems = []", f"{TH}::test_wrong_price_in_text_is_corrected_then_falls_back"),
    (A, "    if args.product_id not in state.known_products:", "    if False:",
     f"{TH}::test_wrong_price_in_text_is_corrected_then_falls_back"),
    (M, "                history=session.history(settings.history_turns),", "                history=[],",
     f"{TH}::test_takamine_then_pix_keeps_product_in_context"),
    (M, '            if cached.status == "done":\n                return cached.response',
     '            if False:\n                return cached.response', f"{TH}::test_same_request_id_returns_same_answer_without_new_model_call"),
    (M, "        if not session.lock.acquire(blocking=False):", "        if not session.lock.acquire(blocking=True):",
     f"{TH}::test_concurrent_turn_in_same_session_is_409"),
    (M, "            except ProviderUnavailable:\n                session.requests.pop(rid, None)",
     "            except ProviderUnavailable:\n                pass", f"{TH}::test_provider_failures_are_public_errors_and_release_the_request_id"),
    (S, "        if len(self.recent_turns) >= per_minute:", "        if False:", f"{TH}::test_rate_limit_is_429"),
    (O, '        row = con.execute("SELECT * FROM orders WHERE order_id = ? AND customer_id = ?",\n                          (order_id, customer_id)).fetchone()',
     '        row = con.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()',
     f"{TO}::test_cross_profile_equals_non_existent"),
    (M, "        session.reset_context()\n", "", f"{TH}::test_profile_a_sees_order_8_and_profile_b_does_not"),
    (M, "            if session.generation != generation:", "            if False:",
     f"{TH}::test_profile_switch_discards_turn_in_flight"),
    (A, '        cents |= set(money_mentions(s["text"]))', "        pass",
     f"{TH}::test_exact_500_shipping_prepares_handoff"),
    (P, '            for rid in self.by_id[sid]["related_ids"]:', "            for rid in []:",
     f"{TP}::test_related_sections_are_added"),
    (A, '        if state.profile_required:\n            next_action = "choose_profile"',
     '        if False:\n            next_action = "choose_profile"', f"{TH}::test_order_as_visitor_asks_for_profile"),
    (S, "            if self.count >= self.limit:", "            if False:", f"{TH}::test_daily_cap_stops_model_calls"),
    (A, "    problems += product_reference_problems(text, _evidence_text(state))\n", "",
     f"{TH}::test_invented_product_is_never_shown"),
    (A, "        if not _INSTALLMENTS_RE.match(code) and code.casefold() not in tokens:", "        if False:",
     f"{TPM}::test_model_code_without_brand_is_flagged"),
    (A, "    parts = [state.message, *state.known_products.values()]", "    parts = [state.message]",
     f"{TH}::test_product_from_tool_result_or_customer_words_is_accepted"),
    (A, "    parts = [state.message, *state.known_products.values()]",
     "    parts = [*state.known_products.values()]", f"{TH}::test_product_from_tool_result_or_customer_words_is_accepted"),
    (A, "    problems += [f\"promises an action no system performs: '{m.group(0)}'\" for m in _PROMISE_RE.finditer(text)]\n",
     "", f"{TH}::test_promised_action_is_rejected"),
    (C, "ON p.category_id = c.category_id AND p.sellable = 1 ", "ON p.category_id = c.category_id ",
     f"{TH}::test_empty_search_tells_the_model_what_the_store_has"),
    (A, "            if reply.calls and can_fetch:", "            if False:",
     f"{TH}::test_unconfirmed_price_is_fetched_in_the_correction"),
    (C, '                 "availability", "sellable", "created_at",', '                 "status", "availability", "sellable", "created_at",',
     f"{TC}::test_status_column_is_not_public"),
    (C, "        if wanted:\n", "        if False:\n", f"{TC}::test_discover_keeps_only_the_strings_the_customer_asked_for"),
    (FJ, '  if (card.payment_cents != null && card.payment_method && card.payment_method !== "table") {',
     '  if (card.payment_cents != null && card.payment_method) {', TJ),
    (FJ, "  if (card.discount_percent > 0) {", "  if (false) {", TJ),
    (FJ, "  if (!available) return view;", "  if (false) return view;", TJ),
    (B, '    out = usage.get("output", 0) + usage.get("thoughts", 0)', '    out = usage.get("output", 0)',
     f"{TCM}::test_cost_per_turn_bills_thinking_tokens_as_output"),
    (CM, "    return mean_usd_per_turn * turns * conversations", "    return mean_usd_per_turn * conversations",
     f"{TCM}::test_monthly_projection_is_mean_times_turns_times_conversations"),
    (CM, '                + min(gib_s, free["gib_seconds"]) * free["tier1_gib_second_usd"]',
     '                + gib_s * free["tier1_gib_second_usd"]', f"{TCM}::test_cloud_run_gross_and_free_tier"),
]


def main() -> int:
    escaped = 0
    for rel, old, new, test in MUTATIONS:
        path = ROOT / rel
        original = path.read_text()
        if original.count(old) != 1:
            print(f"INVALID ANCHOR in {rel}: {old.strip()[:60]!r}")
            return 2
        path.write_text(original.replace(old, new))
        try:
            run = subprocess.run(["timeout", "120", sys.executable, "-m", "pytest", "-q", "-x", test],
                                 cwd=ROOT, capture_output=True, text=True)
        finally:
            path.write_text(original)
        caught = run.returncode != 0
        escaped += not caught
        print(("CAUGHT  " if caught else "ESCAPED ") + f"{rel}: {new.strip()[:70]}")
    print(f"{len(MUTATIONS) - escaped}/{len(MUTATIONS)} mutations caught")
    return 1 if escaped else 0


if __name__ == "__main__":
    sys.exit(main())
