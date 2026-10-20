"""Order status rules: one step at a time, cancel only before shipping, final states are final."""
from collections.abc import Callable
from itertools import product as all_pairs

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.user import User, UserRole
from tests.helpers import Headers, place_order, send_simultaneously

S = OrderStatus
ALLOWED = {
    (S.PENDING, S.CONFIRMED),
    (S.PENDING, S.CANCELLED),
    (S.CONFIRMED, S.IN_TRANSIT),
    (S.CONFIRMED, S.CANCELLED),
    (S.IN_TRANSIT, S.DELIVERED),
}
# The path an order takes through the API to reach each status.
PATH_TO = {
    S.PENDING: [],
    S.CONFIRMED: [S.CONFIRMED],
    S.IN_TRANSIT: [S.CONFIRMED, S.IN_TRANSIT],
    S.DELIVERED: [S.CONFIRMED, S.IN_TRANSIT, S.DELIVERED],
    S.CANCELLED: [S.CANCELLED],
}


@pytest.fixture
def order_in(
    client: TestClient,
    customer: User,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> Callable[[OrderStatus], tuple[int, Product]]:
    """Place a 10-unit order and walk it through the API to the given status."""

    def _order_in(status: OrderStatus) -> tuple[int, Product]:
        product = make_product(quantity_on_hand=100)
        order_id = place_order(client, auth_headers(customer), (product, 10)).json()["id"]
        for step in PATH_TO[status]:
            response = client.patch(
                f"/api/orders/{order_id}/status", json={"status": step.value}, headers=auth_headers(distributor)
            )
            assert response.status_code == 200, response.json()
        return order_id, product

    return _order_in


@pytest.mark.parametrize(
    "current, requested",
    list(all_pairs(S, S)),
    ids=[f"{a.value}-to-{b.value}" for a, b in all_pairs(S, S)],
)
def test_status_change_follows_the_rules(
    client: TestClient,
    db: Session,
    distributor: User,
    auth_headers: Headers,
    order_in: Callable[[OrderStatus], tuple[int, Product]],
    current: OrderStatus,
    requested: OrderStatus,
) -> None:
    order_id, product = order_in(current)
    db.refresh(product)
    stock_before = product.quantity_on_hand

    response = client.patch(
        f"/api/orders/{order_id}/status", json={"status": requested.value}, headers=auth_headers(distributor)
    )

    db.expire_all()
    order = db.get(Order, order_id)
    if current == requested or (current, requested) in ALLOWED:
        assert response.status_code == 200
        assert order.status == requested
    else:
        assert response.status_code == 409
        assert order.status == current
        assert db.get(Product, product.id).quantity_on_hand == stock_before


@pytest.mark.parametrize("before_shipping", [S.PENDING, S.CONFIRMED])
def test_cancelling_before_shipping_restores_stock(
    client: TestClient,
    db: Session,
    distributor: User,
    auth_headers: Headers,
    order_in: Callable[[OrderStatus], tuple[int, Product]],
    before_shipping: OrderStatus,
) -> None:
    order_id, product = order_in(before_shipping)

    client.patch(f"/api/orders/{order_id}/status", json={"status": "CANCELLED"}, headers=auth_headers(distributor))

    db.refresh(product)
    assert product.quantity_on_hand == 100


@pytest.mark.parametrize("shipped", [S.IN_TRANSIT, S.DELIVERED])
def test_shipped_orders_cannot_be_cancelled_or_restocked(
    client: TestClient,
    db: Session,
    distributor: User,
    auth_headers: Headers,
    order_in: Callable[[OrderStatus], tuple[int, Product]],
    shipped: OrderStatus,
) -> None:
    order_id, product = order_in(shipped)

    response = client.patch(
        f"/api/orders/{order_id}/status", json={"status": "CANCELLED"}, headers=auth_headers(distributor)
    )

    assert response.status_code == 409
    db.refresh(product)
    assert product.quantity_on_hand == 90


def test_rejection_explains_the_allowed_next_steps(
    client: TestClient,
    distributor: User,
    auth_headers: Headers,
    order_in: Callable[[OrderStatus], tuple[int, Product]],
) -> None:
    order_id, _ = order_in(S.PENDING)

    response = client.patch(
        f"/api/orders/{order_id}/status", json={"status": "DELIVERED"}, headers=auth_headers(distributor)
    )

    assert response.json()["detail"] == (
        f"Order #{order_id} can't go from PENDING to DELIVERED. Next it can be CONFIRMED or CANCELLED."
    )


def test_rejection_says_when_a_status_is_final(
    client: TestClient,
    distributor: User,
    auth_headers: Headers,
    order_in: Callable[[OrderStatus], tuple[int, Product]],
) -> None:
    order_id, _ = order_in(S.DELIVERED)

    response = client.patch(
        f"/api/orders/{order_id}/status", json={"status": "IN_TRANSIT"}, headers=auth_headers(distributor)
    )

    assert response.json()["detail"] == f"Order #{order_id} is DELIVERED, which is final. Its status can't change."


@pytest.mark.parametrize(
    "status, expected_next",
    [
        (S.PENDING, ["CONFIRMED", "CANCELLED"]),
        (S.CONFIRMED, ["IN_TRANSIT", "CANCELLED"]),
        (S.IN_TRANSIT, ["DELIVERED"]),
        (S.DELIVERED, []),
        (S.CANCELLED, []),
    ],
)
def test_orders_report_their_allowed_next_statuses(
    client: TestClient,
    customer: User,
    auth_headers: Headers,
    order_in: Callable[[OrderStatus], tuple[int, Product]],
    status: OrderStatus,
    expected_next: list[str],
) -> None:
    order_id, _ = order_in(status)

    single = client.get(f"/api/orders/{order_id}", headers=auth_headers(customer)).json()
    listed = client.get("/api/orders", headers=auth_headers(customer)).json()

    assert single["next_statuses"] == expected_next
    assert [o["next_statuses"] for o in listed if o["id"] == order_id] == [expected_next]


def test_shipping_and_cancelling_at_the_same_moment_lets_exactly_one_win(
    db: Session,
    make_user: Callable[..., User],
    auth_headers: Headers,
    order_in: Callable[[OrderStatus], tuple[int, Product]],
) -> None:
    order_id, product = order_in(S.CONFIRMED)
    shipper, canceller = make_user(UserRole.DISTRIBUTOR), make_user(UserRole.ADMIN)
    url = f"/api/orders/{order_id}/status"

    statuses = send_simultaneously(
        [
            ("PATCH", url, auth_headers(shipper), {"status": "IN_TRANSIT"}),
            ("PATCH", url, auth_headers(canceller), {"status": "CANCELLED"}),
        ]
    )

    # Whichever runs second sees the other's status: IN_TRANSIT can't be cancelled, and
    # CANCELLED is final.
    assert sorted(statuses) == [200, 409]
    db.expire_all()
    final = db.get(Order, order_id).status
    stock = db.get(Product, product.id).quantity_on_hand
    assert (final, stock) in {(S.IN_TRANSIT, 90), (S.CANCELLED, 100)}
