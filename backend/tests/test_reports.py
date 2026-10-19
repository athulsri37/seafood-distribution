from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.models.product import Product
from app.models.user import User, UserRole
from tests.helpers import Headers, place_order


def test_dashboard_on_empty_database_returns_zeros(
    client: TestClient, admin: User, auth_headers: Headers
) -> None:
    response = client.get("/api/reports/dashboard", headers=auth_headers(admin))

    assert response.status_code == 200
    assert response.json() == {
        "total_orders": 0,
        "total_revenue": 0.0,
        "total_customers": 0,
        "low_stock_count": 0,
        "sales_by_status": [],
        "top_products": [],
    }


def test_dashboard_aggregates_orders_customers_and_products(
    client: TestClient,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    admin = make_user(UserRole.ADMIN)
    alice, bob = make_user(UserRole.CUSTOMER), make_user(UserRole.CUSTOMER)
    salmon = make_product(name="Salmon", price_per_unit="10.00", quantity_on_hand=100)
    shrimp = make_product(name="Shrimp", price_per_unit="5.00", quantity_on_hand=100)
    make_product(name="Scallops", quantity_on_hand=5, reorder_threshold=25)

    place_order(client, auth_headers(alice), (salmon, 3), (shrimp, 10))  # 30 + 50
    confirmed = place_order(client, auth_headers(bob), (salmon, 2)).json()["id"]  # 20
    client.patch(f"/api/orders/{confirmed}/status", json={"status": "CONFIRMED"}, headers=auth_headers(admin))

    body = client.get("/api/reports/dashboard", headers=auth_headers(admin)).json()

    assert body["total_orders"] == 2
    assert body["total_revenue"] == pytest.approx(100.0)
    assert body["total_customers"] == 2
    assert body["low_stock_count"] == 1
    by_status = {row["status"]: row for row in body["sales_by_status"]}
    assert by_status["PENDING"]["order_count"] == 1
    assert by_status["PENDING"]["total_revenue"] == pytest.approx(80.0)
    assert by_status["CONFIRMED"]["total_revenue"] == pytest.approx(20.0)
    assert [(p["product_name"], p["units_sold"]) for p in body["top_products"]] == [
        ("Shrimp", 10),
        ("Salmon", 5),
    ]
    assert body["top_products"][1]["revenue"] == pytest.approx(50.0)


def test_top_products_lists_at_most_five(
    client: TestClient,
    admin: User,
    customer: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    products = [make_product() for _ in range(7)]
    place_order(client, auth_headers(customer), *[(p, 1) for p in products])

    body = client.get("/api/reports/dashboard", headers=auth_headers(admin)).json()

    assert len(body["top_products"]) == 5


@pytest.mark.xfail(reason="B13: revenue includes cancelled orders")
def test_revenue_excludes_cancelled_orders(
    client: TestClient,
    admin: User,
    customer: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    product = make_product(price_per_unit="10.00")
    place_order(client, auth_headers(customer), (product, 1))
    cancelled = place_order(client, auth_headers(customer), (product, 5)).json()["id"]
    client.patch(f"/api/orders/{cancelled}/status", json={"status": "CANCELLED"}, headers=auth_headers(admin))

    body = client.get("/api/reports/dashboard", headers=auth_headers(admin)).json()

    assert body["total_revenue"] == pytest.approx(10.0)
