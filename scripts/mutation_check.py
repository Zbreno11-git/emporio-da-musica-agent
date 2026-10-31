"""Rede curada de mutações: cada mutação é um defeito real que um teste específico precisa derrubar.

Para cada item: aplica a troca no arquivo, roda só o teste esperado e restaura o original.
Uma mutação que "escapa" (o teste continua verde) prova que o teste não protege aquela regra.
Uso: .venv/bin/python scripts/mutation_check.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
Q, I, C = "app/tools/quote.py", "scripts/import_snapshot.py", "app/tools/catalog.py"
TQ, TI, TC = "tests/domain/test_quote.py", "tests/domain/test_import_snapshot.py", "tests/tools/test_catalog_sql.py"

MUTATIONS = [
    # (arquivo, trecho original, defeito, teste que tem de cair)
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
    (I, "        staging.rename(out)\n", "        staging.rename(out)\n        raise ImportError_('x')\n",
     f"{TI}::test_failed_import_preserves_previous_build"),
    (I, '    demo_orders = [o for o in data["orders"] if o["customer_id"] in demo_ids]',
     '    demo_orders = list(data["orders"])',
     f"{TI}::test_orders_db_has_no_personal_columns_and_only_demo_customers"),
    (C, "    return sqlite3.SQLITE_DENY  # inclui", "    return sqlite3.SQLITE_OK  # inclui",
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
]


def main() -> int:
    escaped = 0
    for rel, old, new, test in MUTATIONS:
        path = ROOT / rel
        original = path.read_text()
        if original.count(old) != 1:
            print(f"ÂNCORA INVÁLIDA em {rel}: {old.strip()[:60]!r}")
            return 2
        path.write_text(original.replace(old, new))
        try:
            run = subprocess.run(["timeout", "120", sys.executable, "-m", "pytest", "-q", "-x", test],
                                 cwd=ROOT, capture_output=True, text=True)
        finally:
            path.write_text(original)
        caught = run.returncode != 0
        escaped += not caught
        print(("PEGA   " if caught else "ESCAPA ") + f"{rel}: {new.strip()[:70]}")
    print(f"{len(MUTATIONS) - escaped}/{len(MUTATIONS)} mutações pegas")
    return 1 if escaped else 0


if __name__ == "__main__":
    sys.exit(main())
