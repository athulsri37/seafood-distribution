"""Low stock is decided in SQL, so the API never loads every product to find the low ones."""
from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.product import Product
from app.models.user import User
from tests.helpers import Headers, capture_queries

LOW_STOCK_SQL = "products.quantity_on_hand <= products.reorder_threshold"


def make_mixed_stock(make_product: Callable[..., Product]) -> None:
    make_product(quantity_on_hand=100, reorder_threshold=20, name="Plenty")
    make_product(quantity_on_hand=20, reorder_threshold=20, name="At threshold")
    make_product(quantity_on_hand=0, reorder_threshold=5, name="Sold out")
    for n in range(10):
        make_product(quantity_on_hand=500, reorder_threshold=10, name=f"Well stocked {n}")


def test_low_stock_filter_runs_in_sql_and_returns_only_low_products(
    client: TestClient, customer: User, make_product: Callable[..., Product], auth_headers: Headers
) -> None:
    make_mixed_stock(make_product)

    with capture_queries() as statements:
        response = client.get("/api/products", params={"low_stock_only": True}, headers=auth_headers(customer))

    assert sorted(p["name"] for p in response.json()) == ["At threshold", "Sold out"]
    assert all(p["is_low_stock"] for p in response.json())
    assert any(LOW_STOCK_SQL in s for s in statements)


def test_unfiltered_list_still_flags_each_product(
    client: TestClient, customer: User, make_product: Callable[..., Product], auth_headers: Headers
) -> None:
    make_mixed_stock(make_product)

    products = client.get("/api/products", headers=auth_headers(customer)).json()

    assert len(products) == 13
    assert {p["name"] for p in products if p["is_low_stock"]} == {"At threshold", "Sold out"}


def test_dashboard_counts_low_stock_in_sql(
    client: TestClient, admin: User, make_product: Callable[..., Product], auth_headers: Headers
) -> None:
    make_mixed_stock(make_product)

    with capture_queries() as statements:
        body = client.get("/api/reports/dashboard", headers=auth_headers(admin)).json()

    assert body["low_stock_count"] == 2
    low_stock_queries = [s for s in statements if LOW_STOCK_SQL in s]
    assert len(low_stock_queries) == 1 and "count(" in low_stock_queries[0].lower()
