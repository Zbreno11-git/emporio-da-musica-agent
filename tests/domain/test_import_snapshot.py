"""Importador: snapshot real contra os oráculos e validações com dados sintéticos."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from scripts.import_snapshot import HEADERS, ImportError_, build


def _rows(db: Path, sql: str, *params) -> list[sqlite3.Row]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()


# --- snapshot real -----------------------------------------------------------------------------------

def test_manifest_counts_match_oracles(snapshot_build, oracles):
    manifest = json.loads((snapshot_build / "manifest.json").read_text())
    assert manifest["counts"] == oracles["counts"]
    assert manifest["sellable_count"] == oracles["sellable_count"] == 61
    assert manifest["active_promotions"] == 4


def test_catalog_prices_match_oracles(snapshot_build, oracles):
    db = snapshot_build / "catalog.db"
    for o in oracles["products"]:
        (row,) = _rows(db, "SELECT * FROM products WHERE product_id = ?", o["product_id"])
        assert (row["base_cents"], row["promotion_percent"], row["offer_cents"], row["pix_cents"]) == (
            o["base_cents"], o["promotion_percent"], o["offer_cents"], o["pix_cents"]), o["product_id"]
        assert bool(row["sellable"]) is o["saleable"], o["product_id"]


def test_availability_states_of_edge_products(snapshot_build):
    db = snapshot_build / "catalog.db"
    states = {r["product_id"]: r["availability"] for r in
              _rows(db, "SELECT product_id, availability FROM products WHERE product_id IN (96, 130, 136)")}
    assert states == {96: "out_of_stock", 130: "coming_soon", 136: "discontinued"}


def test_orders_match_oracles(snapshot_build, oracles):
    db = snapshot_build / "orders-demo.db"
    for o in oracles["orders"]:
        (row,) = _rows(db, "SELECT * FROM orders WHERE order_id = ?", o["order_id"])
        assert row["customer_id"] == o["customer_id"]
        assert row["status"] == o["status"]
        assert row["total_cents"] == o["total_cents"]
        assert row["estimated_delivery"] == o["estimated_delivery"]
        assert (row["tracking_code"] is not None) is o["has_tracking"]


def test_catalog_db_has_no_private_tables(snapshot_build):
    tables = {r[0] for r in _rows(snapshot_build / "catalog.db", "SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == {"categories", "products", "promotions"}


def test_orders_db_has_no_personal_columns_and_only_demo_customers(snapshot_build):
    db = snapshot_build / "orders-demo.db"
    tables = {r[0] for r in _rows(db, "SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == {"profiles", "orders", "order_items"}
    columns = {c[1] for t in tables for c in _rows(db, f"PRAGMA table_info({t})")}
    assert not columns & {"name", "email", "phone", "city"}
    customers = {r[0] for r in _rows(db, "SELECT DISTINCT customer_id FROM orders")}
    assert customers <= {2, 6, 7}


# --- validação com dados sintéticos -------------------------------------------------------------------

def _synthetic(tmp_path: Path, **overrides: list[list[str]]) -> Path:
    data = {
        "categories": [["1", "Violões", "Acústicos"]],
        "products": [["10", "100.5", "Violão Teste", "1", "desc", "3", "active", '{"strings":"nylon"}', "2024-01-01"]],
        "promotions": [["1", "10", "10", "Teste", "1"]],
        "customers": [[str(i), f"Pessoa {i}", f"6799999000{i}", f"p{i}@example.com", "Campo Grande"]
                      for i in (2, 6, 7)],
        "orders": [["1", "2", "2026-01-01", "shipped", "100.5", "pix", "BRAB1234567BR", "2026-01-05", ""]],
        "order_items": [["1", "1", "10"]],
    }
    data.update(overrides)
    src = tmp_path / "src"
    src.mkdir()
    for table, rows in data.items():
        lines = [",".join(HEADERS[table])] + [",".join(f'"{v}"' if "," in v or '"' in v else v
                                                       for v in (c.replace('"', '""') if '"' in c else c for c in r))
                                              for r in rows]
        (src / f"desafio_tecnico_ai_eng - {table}.csv").write_text("﻿" + "\n".join(lines) + "\n")
    return src


def test_synthetic_snapshot_builds_with_bom(tmp_path):
    manifest = build(_synthetic(tmp_path), tmp_path / "out")
    assert manifest["counts"]["products"] == 1
    (row,) = _rows(tmp_path / "out" / "catalog.db", "SELECT offer_cents, pix_cents FROM products")
    assert tuple(row) == (9045, 9045)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"products": [["10", "100.5", "A", "1", "d", "3", "active", "{}", "2024-01-01"],
                       ["10", "1", "B", "1", "d", "3", "active", "{}", "2024-01-01"]]}, "duplicado"),
        ({"products": [["10", "100.5", "A", "9", "d", "3", "active", "{}", "2024-01-01"]]}, "category_id=9"),
        ({"products": [["10", "R$ 100", "A", "1", "d", "3", "active", "{}", "2024-01-01"]]}, "monetário"),
        ({"products": [["10", "100", "A", "1", "d", "3", "active", "{quebrado", "2024-01-01"]]}, "JSON"),
        ({"promotions": [["1", "10", "10", "X", "1"], ["2", "10", "5", "Y", "1"]]}, "segunda promoção ativa"),
        ({"order_items": [["1", "1", "99"]]}, "product_id=99"),
    ],
)
def test_invalid_rows_abort_with_line_and_reason(tmp_path, override, message):
    with pytest.raises(ImportError_, match=message) as exc:
        build(_synthetic(tmp_path, **override), tmp_path / "out")
    assert "linha" in str(exc.value)


def test_failed_import_preserves_previous_build(tmp_path):
    out = tmp_path / "out"
    (tmp_path / "ok").mkdir()
    (tmp_path / "bad").mkdir()
    first = build(_synthetic(tmp_path / "ok"), out)
    bad = _synthetic(tmp_path / "bad", order_items=[["1", "1", "99"]])
    with pytest.raises(ImportError_):
        build(bad, out)
    assert json.loads((out / "manifest.json").read_text())["dataset_id"] == first["dataset_id"]
    assert not list(tmp_path.glob(".build-*"))
