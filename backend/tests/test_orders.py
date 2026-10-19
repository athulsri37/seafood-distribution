from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.product import Product
from app.models.user import User, UserRole
from tests.helpers import Headers, place_order


def stock_of(db: Session, product: Product) -> int:
    db.refresh(product)
    return product.quantity_on_hand


def test_order_deducts_stock_and_totals_line_items(
    client: TestClient,
    db: Session,
    customer: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    salmon = make_product(quantity_on_hand=100, price_per_unit="14.99")
    shrimp = make_product(quantity_on_hand=50, price_per_unit="11.49")

    response = place_order(client, auth_headers(customer), (salmon, 10), (shrimp, 4))

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["total_amount"] == pytest.approx(14.99 * 10 + 11.49 * 4)
    assert body["customer"]["id"] == customer.id
    assert stock_of(db, salmon) == 90
    assert stock_of(db, shrimp) == 46


def test_order_keeps_price_paid_after_product_price_changes(
    client: TestClient,
    db: Session,
    customer: User,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    tuna = make_product(price_per_unit="19.99")
    order_id = place_order(client, auth_headers(customer), (tuna, 2)).json()["id"]

    client.patch(f"/api/products/{tuna.id}", json={"price_per_unit": 25.0}, headers=auth_headers(distributor))
    order = client.get(f"/api/orders/{order_id}", headers=auth_headers(customer)).json()

    assert order["items"][0]["unit_price"] == 19.99
    assert order["total_amount"] == pytest.approx(39.98)


def test_order_with_insufficient_stock_saves_nothing(
    client: TestClient,
    db: Session,
    customer: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    in_stock = make_product(quantity_on_hand=100)
    scarce = make_product(quantity_on_hand=3)

    # The first line succeeds before the second fails, so this checks the rollback.
    response = place_order(client, auth_headers(customer), (in_stock, 10), (scarce, 5))

    assert response.status_code == 400
    assert stock_of(db, in_stock) == 100
    assert stock_of(db, scarce) == 3
    assert db.query(Order).count() == 0


def test_order_for_unknown_product_returns_404(
    client: TestClient, db: Session, customer: User, auth_headers: Headers
) -> None:
    response = client.post(
        "/api/orders", json={"items": [{"product_id": 999, "quantity": 1}]}, headers=auth_headers(customer)
    )

    assert response.status_code == 404
    assert db.query(Order).count() == 0


def test_order_without_items_is_rejected(client: TestClient, customer: User, auth_headers: Headers) -> None:
    response = client.post("/api/orders", json={"items": []}, headers=auth_headers(customer))

    assert response.status_code == 400


@pytest.mark.parametrize("quantity", [0, -1])
def test_order_line_quantity_must_be_positive(
    client: TestClient,
    customer: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
    quantity: int,
) -> None:
    response = place_order(client, auth_headers(customer), (make_product(), quantity))

    assert response.status_code == 422


def test_customer_sees_only_own_orders_and_staff_see_all(
    client: TestClient,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    alice, bob = make_user(UserRole.CUSTOMER), make_user(UserRole.CUSTOMER)
    product = make_product()
    place_order(client, auth_headers(alice), (product, 1))
    place_order(client, auth_headers(bob), (product, 1))

    alice_view = client.get("/api/orders", headers=auth_headers(alice)).json()
    staff_view = client.get("/api/orders", headers=auth_headers(make_user(UserRole.DISTRIBUTOR))).json()

    assert [o["customer"]["id"] for o in alice_view] == [alice.id]
    assert len(staff_view) == 2


def test_customer_cannot_open_another_customers_order(
    client: TestClient,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    alice, bob = make_user(UserRole.CUSTOMER), make_user(UserRole.CUSTOMER)
    order_id = place_order(client, auth_headers(alice), (make_product(), 1)).json()["id"]

    response = client.get(f"/api/orders/{order_id}", headers=auth_headers(bob))

    assert response.status_code == 403


def test_cancelling_restores_stock_once(
    client: TestClient,
    db: Session,
    customer: User,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    product = make_product(quantity_on_hand=100)
    order_id = place_order(client, auth_headers(customer), (product, 30)).json()["id"]
    url = f"/api/orders/{order_id}/status"

    first = client.patch(url, json={"status": "CANCELLED"}, headers=auth_headers(distributor))
    second = client.patch(url, json={"status": "CANCELLED"}, headers=auth_headers(distributor))

    assert first.status_code == 200
    assert first.json()["status"] == "CANCELLED"
    assert second.status_code == 200
    assert stock_of(db, product) == 100


def test_status_moves_forward_through_pipeline(
    client: TestClient,
    customer: User,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    order_id = place_order(client, auth_headers(customer), (make_product(), 1)).json()["id"]

    for status in ("CONFIRMED", "IN_TRANSIT", "DELIVERED"):
        response = client.patch(
            f"/api/orders/{order_id}/status", json={"status": status}, headers=auth_headers(distributor)
        )
        assert response.status_code == 200
        assert response.json()["status"] == status


@pytest.mark.xfail(reason="B8: a cancelled order can be reopened without taking stock off again")
def test_cancelled_order_cannot_be_reopened(
    client: TestClient,
    customer: User,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    order_id = place_order(client, auth_headers(customer), (make_product(), 1)).json()["id"]
    url = f"/api/orders/{order_id}/status"
    client.patch(url, json={"status": "CANCELLED"}, headers=auth_headers(distributor))

    response = client.patch(url, json={"status": "PENDING"}, headers=auth_headers(distributor))

    assert response.status_code == 409
