"""Import the Artefact snapshot (6 CSVs) into the demo databases.

Writes to `--out` (default `data/build/`):
- catalog.db       categories, products (with materialized prices) and promotions. This is the only
                   database the model-generated SQL can read.
- orders-demo.db   fictitious profiles, plus orders and items of the customers mapped to the demo only,
                   without name, e-mail, phone or city.
- manifest.json    SHA-256 of the sources, row counts and importer version.

Any violation (header, duplicate key, orphan reference, money format, JSON, two active promotions on the
same product) stops the import with file, line and reason. New files are assembled in a temporary
directory and only replace the previous set when everything passes.

Usage: .venv/bin/python scripts/import_snapshot.py --source <challenge ZIP | directory with the CSVs>
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
import zipfile
from datetime import date
from decimal import InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.tools.quote import availability, price, to_cents  # noqa: E402

IMPORTER_VERSION = "1"
DEFAULT_SOURCE = ROOT / "_private_inputs" / "challenge"
DEFAULT_OUT = ROOT / "data" / "build"

HEADERS = {
    "categories": ["category_id", "name", "description"],
    "products": ["product_id", "price_brl", "name", "category_id", "description", "stock_quantity", "status",
                 "specs", "created_at"],
    "promotions": ["promotion_id", "product_id", "discount_percent", "description", "is_active"],
    "customers": ["customer_id", "name", "phone", "email", "city"],
    "orders": ["order_id", "customer_id", "order_date", "status", "total_brl", "payment_method", "tracking_code",
               "estimated_delivery", "notes"],
    "order_items": ["order_id", "quantity", "product_id"],
}
PRODUCT_STATUSES = {"active", "discontinued", "coming_soon"}
ORDER_STATUSES = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
PAYMENT_RE = re.compile(r"^(pix|debit|boleto|credit_(?:[1-9]|1[0-2])x)$")
TRACKING_RE = re.compile(r"^BR[0-9A-Z]{9}BR$")

# Fictitious demo profiles. The real customer identity lives only in this internal mapping.
# Labels are customer-facing, so they are in Portuguese.
DEMO_PROFILES = [
    {"alias": "demo-a", "customer_id": 2, "label": "Cliente A · pedido em transporte"},
    {"alias": "demo-b", "customer_id": 6, "label": "Cliente B · pedido confirmado"},
    {"alias": "demo-c", "customer_id": 7, "label": "Cliente C · pedidos com cancelamento"},
]


class SnapshotError(Exception):
    """Validation failure with a file and line reference."""


def fail(table: str, line: int | None, reason: str) -> None:
    where = f"{table}.csv" + (f", line {line}" if line is not None else "")
    raise SnapshotError(f"{where}: {reason}")


def _table_name(filename: str) -> str | None:
    name = unicodedata.normalize("NFC", os.path.basename(filename))
    for table in HEADERS:
        if name.endswith(f" - {table}.csv"):
            return table
    return None


def read_sources(source: Path) -> dict[str, tuple[bytes, str]]:
    """Return {table: (bytes, source name)}, requiring exactly one file per table."""
    found: dict[str, list[tuple[bytes, str]]] = {t: [] for t in HEADERS}
    if source.is_file() and zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as z:
            for member in z.namelist():
                table = _table_name(member)
                if table:
                    found[table].append((z.read(member), member))
    elif source.is_dir():
        for path in sorted(source.rglob("*.csv")):
            table = _table_name(path.name)
            if table:
                found[table].append((path.read_bytes(), str(path.relative_to(source))))
    else:
        raise SnapshotError(f"source not found or not a ZIP/directory: {source}")
    for table, matches in found.items():
        if len(matches) != 1:
            raise SnapshotError(f"expected exactly 1 file '* - {table}.csv', found {len(matches)}")
    return {t: m[0] for t, m in found.items()}


def parse_csv(table: str, raw: bytes) -> list[tuple[int, dict[str, str]]]:
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != HEADERS[table]:
        fail(table, 1, f"header {reader.fieldnames} differs from expected {HEADERS[table]}")
    return [(i, row) for i, row in enumerate(reader, start=2)]


def _int(table: str, line: int, field: str, value: str, minimum: int = 0) -> int:
    if not re.fullmatch(r"-?\d+", value.strip()):
        fail(table, line, f"{field} is not an integer: {value!r}")
    n = int(value)
    if n < minimum:
        fail(table, line, f"{field} below {minimum}: {n}")
    return n


def _cents(table: str, line: int, field: str, value: str) -> int:
    if not re.fullmatch(r"\d+(\.\d{1,2})?", value.strip()):
        fail(table, line, f"{field} is not a valid money amount: {value!r}")
    try:
        return to_cents(value)
    except (InvalidOperation, ValueError) as exc:
        fail(table, line, f"invalid {field}: {exc}")
        raise


def _date(table: str, line: int, field: str, value: str, optional: bool = False) -> str | None:
    if optional and not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip()).isoformat()
    except ValueError:
        fail(table, line, f"{field} is not an ISO date: {value!r}")
        raise


def _unique(table: str, rows: list[tuple[int, dict]], key: str) -> dict[int, tuple[int, dict]]:
    seen: dict[int, tuple[int, dict]] = {}
    for line, row in rows:
        k = _int(table, line, key, row[key], minimum=1)
        if k in seen:
            fail(table, line, f"duplicate {key}={k} (first seen on line {seen[k][0]})")
        seen[k] = (line, row)
    return seen


def search_text(name: str) -> str:
    folded = unicodedata.normalize("NFKD", name.lower())
    return " ".join("".join(c for c in folded if not unicodedata.combining(c)).split())


def validate(sources: dict[str, tuple[bytes, str]]) -> dict:
    raw = {t: parse_csv(t, data) for t, (data, _) in sources.items()}

    categories = _unique("categories", raw["categories"], "category_id")
    products = _unique("products", raw["products"], "product_id")
    promotions = _unique("promotions", raw["promotions"], "promotion_id")
    customers = _unique("customers", raw["customers"], "customer_id")
    orders = _unique("orders", raw["orders"], "order_id")

    cat_rows = [{"category_id": k, "name": r["name"].strip(), "description": r["description"].strip()}
                for k, (_, r) in categories.items()]

    active_promo: dict[int, int] = {}
    promo_rows = []
    for pid_, (line, r) in promotions.items():
        product_id = _int("promotions", line, "product_id", r["product_id"], minimum=1)
        if product_id not in products:
            fail("promotions", line, f"product_id={product_id} does not exist in products")
        pct = _int("promotions", line, "discount_percent", r["discount_percent"], minimum=1)
        if pct >= 100:
            fail("promotions", line, f"discount_percent out of range: {pct}")
        if r["is_active"] not in ("0", "1"):
            fail("promotions", line, f"is_active must be 0 or 1: {r['is_active']!r}")
        is_active = r["is_active"] == "1"
        if is_active:
            if product_id in active_promo:
                fail("promotions", line, f"second active promotion for product_id={product_id}")
            active_promo[product_id] = pct
        promo_rows.append({"promotion_id": pid_, "product_id": product_id, "discount_percent": pct,
                           "description": r["description"].strip(), "is_active": int(is_active)})

    product_rows = []
    for pid, (line, r) in products.items():
        category_id = _int("products", line, "category_id", r["category_id"], minimum=1)
        if category_id not in categories:
            fail("products", line, f"category_id={category_id} does not exist in categories")
        if r["status"] not in PRODUCT_STATUSES:
            fail("products", line, f"unknown status: {r['status']!r}")
        stock = _int("products", line, "stock_quantity", r["stock_quantity"])
        try:
            specs = json.loads(r["specs"])
        except json.JSONDecodeError as exc:
            fail("products", line, f"specs is not valid JSON: {exc}")
        if not isinstance(specs, dict):
            fail("products", line, "specs must be a JSON object")
        base = _cents("products", line, "price_brl", r["price_brl"])
        p = price(base, active_promo.get(pid, 0))
        avail = availability(r["status"], stock)
        product_rows.append({
            "product_id": pid, "category_id": category_id, "name": r["name"].strip(),
            "name_search": search_text(r["name"]), "description": r["description"].strip(),
            "specs": json.dumps(specs, ensure_ascii=False, sort_keys=True), "stock_quantity": stock,
            "status": r["status"], "availability": avail, "sellable": int(avail == "available"),
            "created_at": _date("products", line, "created_at", r["created_at"]),
            "base_cents": p.base_cents, "promotion_percent": p.promotion_percent,
            "offer_cents": p.offer_cents, "pix_cents": p.pix_cents,
        })

    order_rows = []
    for oid, (line, r) in orders.items():
        cid = _int("orders", line, "customer_id", r["customer_id"], minimum=1)
        if cid not in customers:
            fail("orders", line, f"customer_id={cid} does not exist in customers")
        if r["status"] not in ORDER_STATUSES:
            fail("orders", line, f"unknown status: {r['status']!r}")
        if not PAYMENT_RE.match(r["payment_method"]):
            fail("orders", line, f"unknown payment_method: {r['payment_method']!r}")
        tracking = r["tracking_code"].strip() or None
        if tracking and not TRACKING_RE.match(tracking):
            fail("orders", line, f"tracking_code does not follow the manual §5.3 format: {tracking!r}")
        order_rows.append({
            "order_id": oid, "customer_id": cid,
            "order_date": _date("orders", line, "order_date", r["order_date"]), "status": r["status"],
            "total_cents": _cents("orders", line, "total_brl", r["total_brl"]),
            "payment_method": r["payment_method"], "tracking_code": tracking,
            "estimated_delivery": _date("orders", line, "estimated_delivery", r["estimated_delivery"], optional=True),
            "notes": r["notes"].strip() or None,
        })

    item_rows = []
    for line, r in raw["order_items"]:
        oid = _int("order_items", line, "order_id", r["order_id"], minimum=1)
        pid = _int("order_items", line, "product_id", r["product_id"], minimum=1)
        if oid not in orders:
            fail("order_items", line, f"order_id={oid} does not exist in orders")
        if pid not in products:
            fail("order_items", line, f"product_id={pid} does not exist in products")
        item_rows.append({"order_id": oid, "product_id": pid,
                          "product_name": products[pid][1]["name"].strip(),
                          "quantity": _int("order_items", line, "quantity", r["quantity"], minimum=1)})
    orders_with_items = {i["order_id"] for i in item_rows}
    for o in order_rows:
        if o["order_id"] not in orders_with_items:
            fail("orders", orders[o["order_id"]][0], f"order_id={o['order_id']} has no items")

    for profile in DEMO_PROFILES:
        if profile["customer_id"] not in customers:
            raise SnapshotError(f"profile {profile['alias']} points to a missing customer")

    return {"categories": cat_rows, "products": product_rows, "promotions": promo_rows,
            "orders": order_rows, "order_items": item_rows, "customer_count": len(customers)}


CATALOG_SCHEMA = """
CREATE TABLE categories (
  category_id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL);
CREATE TABLE products (
  product_id INTEGER PRIMARY KEY, category_id INTEGER NOT NULL REFERENCES categories(category_id),
  name TEXT NOT NULL, name_search TEXT NOT NULL, description TEXT NOT NULL, specs TEXT NOT NULL,
  stock_quantity INTEGER NOT NULL, status TEXT NOT NULL, availability TEXT NOT NULL,
  sellable INTEGER NOT NULL, created_at TEXT NOT NULL, base_cents INTEGER NOT NULL,
  promotion_percent INTEGER NOT NULL, offer_cents INTEGER NOT NULL, pix_cents INTEGER NOT NULL);
CREATE TABLE promotions (
  promotion_id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products(product_id),
  discount_percent INTEGER NOT NULL, description TEXT NOT NULL, is_active INTEGER NOT NULL);
"""

ORDERS_SCHEMA = """
CREATE TABLE profiles (alias TEXT PRIMARY KEY, customer_id INTEGER NOT NULL UNIQUE, label TEXT NOT NULL);
CREATE TABLE orders (
  order_id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES profiles(customer_id),
  order_date TEXT NOT NULL, status TEXT NOT NULL, total_cents INTEGER NOT NULL, payment_method TEXT NOT NULL,
  tracking_code TEXT, estimated_delivery TEXT, notes TEXT);
CREATE TABLE order_items (
  order_id INTEGER NOT NULL REFERENCES orders(order_id), product_id INTEGER NOT NULL,
  product_name TEXT NOT NULL, quantity INTEGER NOT NULL);
"""


def _insert(con: sqlite3.Connection, table: str, rows: list[dict]) -> None:
    if not rows:
        return
    cols = list(rows[0])
    con.executemany(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                    [tuple(r[c] for c in cols) for r in rows])


def write_databases(data: dict, out_dir: Path) -> dict:
    with sqlite3.connect(out_dir / "catalog.db") as con:
        con.executescript(CATALOG_SCHEMA)
        for table in ("categories", "products", "promotions"):
            _insert(con, table, data[table])
    con.close()

    demo_ids = {p["customer_id"] for p in DEMO_PROFILES}
    demo_orders = [o for o in data["orders"] if o["customer_id"] in demo_ids]
    demo_order_ids = {o["order_id"] for o in demo_orders}
    demo_items = [i for i in data["order_items"] if i["order_id"] in demo_order_ids]
    with sqlite3.connect(out_dir / "orders-demo.db") as con:
        con.executescript(ORDERS_SCHEMA)
        _insert(con, "profiles", DEMO_PROFILES)
        _insert(con, "orders", demo_orders)
        _insert(con, "order_items", demo_items)
    con.close()
    return {"demo_profiles": len(DEMO_PROFILES), "demo_orders": len(demo_orders), "demo_items": len(demo_items)}


def build(source: Path, out: Path) -> dict:
    sources = read_sources(source)
    data = validate(sources)
    out.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".build-", dir=out.parent))
    try:
        staging.chmod(0o755)
        demo = write_databases(data, staging)
        manifest = {
            "importer_version": IMPORTER_VERSION,
            "sources": {t: {"file": unicodedata.normalize("NFC", name), "sha256": hashlib.sha256(raw).hexdigest()}
                        for t, (raw, name) in sorted(sources.items())},
            "counts": {"categories": len(data["categories"]), "products": len(data["products"]),
                       "promotions": len(data["promotions"]), "customers": data["customer_count"],
                       "orders": len(data["orders"]), "order_items": len(data["order_items"])},
            "sellable_count": sum(p["sellable"] for p in data["products"]),
            "active_promotions": sum(p["is_active"] for p in data["promotions"]),
            "demo": demo,
        }
        manifest["dataset_id"] = hashlib.sha256(
            json.dumps(manifest["sources"], sort_keys=True).encode()).hexdigest()[:12]
        (staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        previous = out.with_name(out.name + ".previous")
        if previous.exists():
            shutil.rmtree(previous)
        if out.exists():
            out.rename(previous)
        staging.rename(out)
        if previous.exists():
            shutil.rmtree(previous)
        return manifest
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                        help="original challenge ZIP or a directory containing the 6 CSVs")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        manifest = build(args.source, args.out)
    except SnapshotError as exc:
        print(f"ERROR: import stopped; the previous build was preserved. {exc}", file=sys.stderr)
        return 1
    print(json.dumps({k: manifest[k] for k in ("dataset_id", "counts", "sellable_count", "active_promotions", "demo")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
