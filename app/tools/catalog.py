"""Catalog lookup with model-written SQL, inside limits enforced by the backend.

The model writes a SELECT; the executor:
- opens only `catalog.db`, read-only and with `query_only`;
- installs a deny-by-default authorizer: only SELECT, reads of public columns and a short list of
  functions. ATTACH, PRAGMA, writes, metadata, extensions and recursive CTEs are refused at prepare time;
- caps VM steps and time (progress handler) and rows read, even when the SQL has no LIMIT;
- requires a `product_id` column and hydrates products from the canonical table: the name, price and
  availability shown on screen never come from the model's SQL.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Intent = Literal["discover", "lookup", "compare"]

PUBLIC_COLUMNS: dict[str, set[str]] = {
    "categories": {"category_id", "name", "description"},
    "products": {"product_id", "category_id", "name", "name_search", "description", "specs", "stock_quantity",
                 "status", "availability", "sellable", "created_at", "base_cents", "promotion_percent",
                 "offer_cents", "pix_cents"},
    "promotions": {"promotion_id", "product_id", "discount_percent", "description", "is_active"},
}
ALLOWED_FUNCTIONS = {"lower", "upper", "like", "glob", "instr", "length", "substr", "replace", "trim",
                     "coalesce", "ifnull", "abs", "round", "min", "max", "count", "sum", "avg",
                     "json_extract"}
MAX_SQL_CHARS = 2000
MAX_PARAMS = 12
MAX_ROWS_READ = 200
MAX_PRODUCTS = 10
DEFAULT_DISCOVER_CARDS = 3
VM_STEP_INTERVAL = 1_000
MAX_VM_CALLBACKS = 2_000  # ~2 million VM instructions
MAX_QUERY_SECONDS = 2.0

SCHEMA_DESCRIPTION = """Public catalog tables (SQLite, read-only):
- categories(category_id, name, description)
- products(product_id, category_id, name, name_search, description, specs, stock_quantity, status,
  availability, sellable, created_at, base_cents, promotion_percent, offer_cents, pix_cents)
  * name_search: lowercase name without accents, for LIKE.
  * specs: JSON, e.g. json_extract(specs, '$.strings') IN ('nylon','steel').
  * availability: available | out_of_stock | discontinued | coming_soon. sellable = 1 only if available.
  * base_cents: list price; offer_cents: current price (with active promotion); pix_cents: PIX price.
- promotions(promotion_id, product_id, discount_percent, description, is_active)
Categories: 1 Guitarras (electric guitars), 2 Baixos (basses), 3 Baterias e Percussão (drums), 4 Teclados e Pianos
(keyboards), 5 Violões (acoustic guitars), 6 Sopro Madeiras, 7 Sopro Metais, 8 Cordas Orquestrais, 9 Ukuleles.
The result must include a product_id column. Amounts are in cents: R$ 800 = 80000."""


class CatalogQueryError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict:
        return {"error": self.code, "message": self.message}


def _authorizer(action, arg1, arg2, db_name, trigger):
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ:
        allowed = PUBLIC_COLUMNS.get(arg1)
        if allowed is not None and (arg2 in allowed or arg2 == ""):
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION:
        return sqlite3.SQLITE_OK if (arg2 or "").lower() in ALLOWED_FUNCTIONS else sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_DENY  # includes ATTACH, PRAGMA, writes, RECURSIVE and any new action


def _connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.execute("PRAGMA query_only = ON")
    con.row_factory = sqlite3.Row
    return con


def run_select(db_path: Path, sql: str, params: list | None = None) -> list[int]:
    """Run the model's SELECT and return product_ids in order, without duplicates."""
    params = list(params or [])
    sql = sql.strip().rstrip(";").strip()
    if not sql:
        raise CatalogQueryError("invalid_sql", "empty SQL")
    if len(sql) > MAX_SQL_CHARS:
        raise CatalogQueryError("invalid_sql", f"SQL longer than {MAX_SQL_CHARS} characters")
    if len(params) > MAX_PARAMS or not all(isinstance(p, (int, float, str)) and not isinstance(p, bool)
                                           for p in params):
        raise CatalogQueryError("invalid_sql", "params must be up to 12 int, float or str values")

    con = _connect(db_path)
    started = time.monotonic()
    calls = 0

    def progress():
        nonlocal calls
        calls += 1
        return int(calls > MAX_VM_CALLBACKS or time.monotonic() - started > MAX_QUERY_SECONDS)

    con.set_authorizer(_authorizer)
    con.set_progress_handler(progress, VM_STEP_INTERVAL)
    try:
        cur = con.execute(sql, params)
        if cur.description is None or "product_id" not in [d[0] for d in cur.description]:
            raise CatalogQueryError("missing_product_id", "the SELECT must return a product_id column")
        rows = cur.fetchmany(MAX_ROWS_READ)
    except CatalogQueryError:
        raise
    except sqlite3.DatabaseError as exc:
        msg = str(exc)
        if "interrupted" in msg:
            raise CatalogQueryError("too_expensive", "query exceeded the execution budget; add filters") from None
        if "not authorized" in msg or "prohibited" in msg:
            raise CatalogQueryError("forbidden", "query not allowed: only SELECT on the public tables") from None
        raise CatalogQueryError("invalid_sql", msg) from None
    except sqlite3.ProgrammingError as exc:
        raise CatalogQueryError("invalid_sql", str(exc)) from None
    finally:
        con.close()

    ids: list[int] = []
    for row in rows:
        value = row["product_id"]
        if isinstance(value, int) and value not in ids:
            ids.append(value)
    return ids


def attribute(category_id: int, name: str, specs: dict) -> str:
    """A short, verifiable attribute for the product card (customer-facing, in Portuguese)."""
    strings = {"nylon": "nylon", "steel": "aço"}.get(str(specs.get("strings", "")).lower())
    if category_id == 9:
        for size, label in (("soprano", "soprano"), ("concert", "concert"), ("tenor", "tenor"),
                            ("bar", "barítono")):
            if size in search_name(name):
                return f"Ukulele {label}"
        return "Ukulele"
    if category_id == 5 and strings:
        electric = str(specs.get("electronics", "no")).lower() not in ("no", "")
        return f"Cordas de {strings}" + (" · elétrico" if electric else "")
    if category_id in (1, 2) and specs.get("strings"):
        return f"{specs['strings']} cordas"
    if category_id == 3 and specs.get("pieces"):
        return f"{specs['pieces']} peças"
    if category_id == 4 and specs.get("keys"):
        return f"{specs['keys']} teclas"
    return ""


def search_name(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in folded if not unicodedata.combining(c))


def hydrate(db_path: Path, product_ids: list[int]) -> list[dict]:
    """Read the facts allowed on screen from the canonical table, in the requested order."""
    if not product_ids:
        return []
    con = _connect(db_path)
    try:
        marks = ",".join("?" * len(product_ids))
        rows = con.execute(
            f"SELECT p.*, c.name AS category_name FROM products p JOIN categories c USING (category_id) "
            f"WHERE p.product_id IN ({marks})", product_ids).fetchall()
    finally:
        con.close()
    by_id = {r["product_id"]: r for r in rows}
    out = []
    for pid in product_ids:
        r = by_id.get(pid)
        if r is None:
            continue
        specs = json.loads(r["specs"])
        out.append({
            "product_id": pid, "name": r["name"], "category": r["category_name"],
            "attribute": attribute(r["category_id"], r["name"], specs), "availability": r["availability"],
            "base_cents": r["base_cents"], "discount_percent": r["promotion_percent"] if r["sellable"] else 0,
            "offer_cents": r["offer_cents"], "pix_cents": r["pix_cents"],
            "description": r["description"], "specs": specs,
        })
    return out


_BUDGET_RE = re.compile(r"(?:at[eé]|no m[aá]ximo|menos de|abaixo de)\s*r?\$?\s*([\d.]+(?:,\d{1,2})?)\s*(mil)?",
                        re.IGNORECASE)


def budget_from_message(message: str) -> tuple[int, bool] | None:
    """Explicit budget cap in cents and whether it refers to PIX. E.g. "até R$ 800" -> (80000, False)."""
    m = _BUDGET_RE.search(message)
    if not m:
        return None
    number = m.group(1).replace(".", "").replace(",", ".")
    try:
        value = float(number) * (1000 if m.group(2) else 1)
    except ValueError:
        return None
    return round(value * 100), bool(re.search(r"\bpix\b", message, re.IGNORECASE))


@dataclass
class CatalogResult:
    products: list[dict]
    dropped_unavailable: int
    dropped_over_budget: int

    def to_dict(self) -> dict:
        return {"products": self.products, "dropped_unavailable": self.dropped_unavailable,
                "dropped_over_budget": self.dropped_over_budget}


def query_catalog(db_path: Path, sql: str, params: list | None, intent: Intent,
                  user_message: str = "", limit: int | None = None) -> CatalogResult:
    ids = run_select(db_path, sql, params)
    products = hydrate(db_path, ids[:MAX_ROWS_READ])
    dropped_unavailable = dropped_budget = 0
    if intent == "discover":
        # Discovery only offers what is for sale and within the cap the customer stated.
        sellable = [p for p in products if p["availability"] == "available"]
        dropped_unavailable = len(products) - len(sellable)
        products = sellable
        budget = budget_from_message(user_message)
        if budget:
            cap, on_pix = budget
            within = [p for p in products if (p["pix_cents"] if on_pix else p["offer_cents"]) <= cap]
            dropped_budget = len(products) - len(within)
            products = within
        products = products[: min(limit or DEFAULT_DISCOVER_CARDS, MAX_PRODUCTS)]
    else:
        products = products[:MAX_PRODUCTS]
    return CatalogResult(products, dropped_unavailable, dropped_budget)
