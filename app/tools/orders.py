"""Order lookup bound to the session's demo profile.

The model only passes an order number. The customer id comes from the server session and goes into a
parameterized query, so an order of another profile and a non-existent order produce the same answer.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

NOT_AVAILABLE = {"ok": True, "found": False,
                 "message": "No order with this number is available for the selected profile."}


def _connect(db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def list_profiles(db: Path) -> list[dict]:
    con = _connect(db)
    try:
        return [{"alias": r["alias"], "label": r["label"]}
                for r in con.execute("SELECT alias, label FROM profiles ORDER BY alias")]
    finally:
        con.close()


def resolve_profile(db: Path, alias: str) -> int | None:
    con = _connect(db)
    try:
        row = con.execute("SELECT customer_id FROM profiles WHERE alias = ?", (alias,)).fetchone()
        return row["customer_id"] if row else None
    finally:
        con.close()


def get_order(db: Path, customer_id: int | None, order_id: int) -> dict:
    if customer_id is None:
        return {"ok": False, "error": "profile_required",
                "message": "The customer must choose a demo profile before an order can be looked up."}
    con = _connect(db)
    try:
        row = con.execute("SELECT * FROM orders WHERE order_id = ? AND customer_id = ?",
                          (order_id, customer_id)).fetchone()
        if row is None:
            return dict(NOT_AVAILABLE)
        items = con.execute("SELECT product_name, quantity FROM order_items WHERE order_id = ? ORDER BY rowid",
                            (order_id,)).fetchall()
    finally:
        con.close()
    return {
        "ok": True, "found": True, "order_id": row["order_id"], "status": row["status"],
        "order_date": row["order_date"], "total_cents": row["total_cents"],
        "payment_method": row["payment_method"], "tracking_code": row["tracking_code"],
        "estimated_delivery": row["estimated_delivery"],
        "estimated_delivery_note": "estimate recorded in the store snapshot, not a live tracking status",
        "store_note": row["notes"],
        "items": [{"name": i["product_name"], "quantity": i["quantity"]} for i in items],
    }
