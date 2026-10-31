"""Catalog SQL executor: violations blocked by code, and legitimate queries."""

from __future__ import annotations

import pytest

from app.tools.catalog import CatalogQueryError, budget_from_message, query_catalog, run_select

NYLON_UP_TO = """
SELECT p.product_id FROM products p
WHERE p.category_id = ? AND json_extract(p.specs, '$.strings') = 'nylon' AND p.sellable = 1 AND p.offer_cents <= ?
ORDER BY p.offer_cents ASC, p.product_id ASC
"""


@pytest.fixture
def catalog(snapshot_build):
    return snapshot_build / "catalog.db"


@pytest.mark.parametrize(
    ("sql", "code"),
    [
        (f"ATTACH DATABASE 'orders-demo.db' AS o", "forbidden"),
        ("UPDATE products SET stock_quantity = 0", "forbidden"),
        ("INSERT INTO categories VALUES (99, 'x', 'y')", "forbidden"),
        ("PRAGMA table_info(products)", "forbidden"),
        ("SELECT name AS product_id FROM sqlite_master", "forbidden"),
        ("SELECT order_id AS product_id FROM orders", "invalid_sql"),  # does not exist in catalog.db
        ("WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM c) SELECT x AS product_id FROM c", "forbidden"),
        ("SELECT load_extension('x') AS product_id", "forbidden"),
        ("SELECT length(randomblob(100000000)) AS product_id", "forbidden"),  # function not on the allowlist
        ("SELECT 1 AS product_id WHERE sqlite_version() <> ''", "forbidden"),
    ],
)
def test_violations_are_blocked(catalog, sql, code):
    with pytest.raises(CatalogQueryError) as exc:
        run_select(catalog, sql)
    assert exc.value.code == code


def test_attach_of_private_orders_db_is_blocked_even_with_real_path(snapshot_build):
    sql = f"ATTACH DATABASE '{snapshot_build / 'orders-demo.db'}' AS o"
    with pytest.raises(CatalogQueryError) as exc:
        run_select(snapshot_build / "catalog.db", sql)
    assert exc.value.code == "forbidden"


def test_expensive_valid_query_is_interrupted(catalog):
    sql = ("SELECT a.product_id FROM products a, products b, products c, products d "
           "ORDER BY a.name || b.name || c.name || d.name")
    with pytest.raises(CatalogQueryError) as exc:
        run_select(catalog, sql)
    assert exc.value.code == "too_expensive"


def test_multiple_statements_are_rejected(catalog):
    with pytest.raises(CatalogQueryError) as exc:
        run_select(catalog, "SELECT product_id FROM products; DELETE FROM products")
    assert exc.value.code in {"invalid_sql", "forbidden"}


def test_product_id_column_is_required(catalog):
    with pytest.raises(CatalogQueryError) as exc:
        run_select(catalog, "SELECT name FROM products")
    assert exc.value.code == "missing_product_id"


def test_rows_read_are_capped_without_limit(catalog, monkeypatch):
    import app.tools.catalog as cat

    monkeypatch.setattr(cat, "MAX_ROWS_READ", 5)
    ids = run_select(catalog, "SELECT product_id FROM products ORDER BY product_id")  # 65 distinct ids, no LIMIT
    assert ids == [81, 82, 83, 84, 85]


def test_nylon_up_to_800(catalog):
    result = query_catalog(catalog, NYLON_UP_TO, [5, 80000], "discover", "Tem violão de nylon até R$ 800?", limit=10)
    assert [p["product_id"] for p in result.products] == [83, 85, 81, 84]
    assert all(p["availability"] == "available" and p["offer_cents"] <= 80000 for p in result.products)
    assert result.products[2]["name"] == "Yamaha C40 Nylon Natural"
    assert result.products[2]["attribute"] == "Cordas de nylon"


def test_discover_drops_unavailable_and_over_budget_even_if_sql_forgets(catalog):
    sql = "SELECT product_id FROM products WHERE category_id = 5 ORDER BY offer_cents"
    result = query_catalog(catalog, sql, [], "discover", "violões até R$ 800", limit=10)
    assert all(p["availability"] == "available" and p["offer_cents"] <= 80000 for p in result.products)
    assert result.dropped_unavailable >= 1  # 96 (out of stock) and 113 (discontinued)


def test_lookup_keeps_unavailable_to_explain_state(catalog):
    result = query_catalog(catalog, "SELECT product_id FROM products WHERE name_search LIKE ?",
                           ["%gf-3d%"], "lookup")
    assert [(p["product_id"], p["availability"]) for p in result.products] == [(96, "out_of_stock")]


def test_lookup_takamine(catalog):
    result = query_catalog(catalog, "SELECT product_id FROM products WHERE name_search LIKE ?",
                           ["%takamine gd20%"], "lookup")
    (p,) = result.products
    assert (p["product_id"], p["offer_cents"], p["pix_cents"]) == (95, 219900, 208905)


def test_ukulele_attribute(catalog):
    (p,) = query_catalog(catalog, "SELECT product_id FROM products WHERE product_id = 127", [], "lookup").products
    assert p["attribute"] == "Ukulele tenor"


@pytest.mark.parametrize(
    ("message", "expected"),
    [("Tem violão de nylon até R$ 800?", (80000, False)), ("algo até R$1.000 no PIX", (100000, True)),
     ("até 2 mil", (200000, False)), ("quanto custa o Takamine?", None)],
)
def test_budget_from_message(message, expected):
    assert budget_from_message(message) == expected
