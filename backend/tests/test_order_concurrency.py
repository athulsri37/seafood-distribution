"""Orders and cancellations that happen at the same moment must never oversell or corrupt stock.

Each request runs in its own thread with its own client, so the API handles them
concurrently against PostgreSQL, the way simultaneous customers would.
"""
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.main import app
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User, UserRole
from tests.helpers import Headers, place_order

Request = tuple[str, str, dict[str, str], dict]  # method, url, headers, json body


def send_simultaneously(requests: list[Request]) -> list[int]:
    """Send every request at the same moment and return the status codes in order."""
    barrier = Barrier(len(requests))

    def send(request: Request) -> int:
        method, url, headers, body = request
        with TestClient(app) as client:
            barrier.wait()
            return client.request(method, url, headers=headers, json=body).status_code

    with ThreadPoolExecutor(max_workers=len(requests)) as pool:
        return list(pool.map(send, requests))


def order_request(headers: dict[str, str], *lines: tuple[Product, int]) -> Request:
    items = [{"product_id": product.id, "quantity": quantity} for product, quantity in lines]
    return ("POST", "/api/orders", headers, {"items": items})


def stock_of(db: Session, product: Product) -> int:
    db.refresh(product)
    return product.quantity_on_hand


def units_in_live_orders(db: Session, product: Product) -> int:
    return (
        db.query(func.coalesce(func.sum(OrderItem.quantity), 0))
        .join(Order)
        .filter(OrderItem.product_id == product.id, Order.status != OrderStatus.CANCELLED)
        .scalar()
    )


def test_simultaneous_orders_never_sell_more_than_is_in_stock(
    db: Session,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    scallops = make_product(quantity_on_hand=5)
    customers = [make_user(UserRole.CUSTOMER) for _ in range(12)]

    statuses = send_simultaneously([order_request(auth_headers(c), (scallops, 1)) for c in customers])

    assert statuses.count(201) == 5
    assert statuses.count(409) == 7
    assert stock_of(db, scallops) == 0
    assert units_in_live_orders(db, scallops) == 5


def test_orders_locking_products_in_opposite_order_do_not_deadlock(
    db: Session,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    salmon, tuna = make_product(quantity_on_hand=100), make_product(quantity_on_hand=100)
    customers = [make_user(UserRole.CUSTOMER) for _ in range(10)]
    requests = [
        order_request(auth_headers(c), (salmon, 1), (tuna, 1))
        if i % 2
        else order_request(auth_headers(c), (tuna, 1), (salmon, 1))
        for i, c in enumerate(customers)
    ]

    statuses = send_simultaneously(requests)

    assert statuses == [201] * 10
    assert stock_of(db, salmon) == 90
    assert stock_of(db, tuna) == 90


def test_simultaneous_cancellations_restore_stock_once(
    client: TestClient,
    db: Session,
    customer: User,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    lobster = make_product(quantity_on_hand=100)
    order_id = place_order(client, auth_headers(customer), (lobster, 30)).json()["id"]
    staff = [make_user(UserRole.DISTRIBUTOR) for _ in range(8)]
    cancel = {"status": "CANCELLED"}

    send_simultaneously([("PATCH", f"/api/orders/{order_id}/status", auth_headers(s), cancel) for s in staff])

    assert stock_of(db, lobster) == 100


def test_stock_stays_consistent_when_a_cancellation_races_new_orders(
    client: TestClient,
    db: Session,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    shrimp = make_product(quantity_on_hand=10)
    first_buyer = make_user(UserRole.CUSTOMER)
    order_id = place_order(client, auth_headers(first_buyer), (shrimp, 10)).json()["id"]
    distributor = make_user(UserRole.DISTRIBUTOR)
    buyers = [make_user(UserRole.CUSTOMER) for _ in range(10)]

    send_simultaneously(
        [("PATCH", f"/api/orders/{order_id}/status", auth_headers(distributor), {"status": "CANCELLED"})]
        + [order_request(auth_headers(b), (shrimp, 1)) for b in buyers]
    )

    # Every unit is either still in stock or in an order that wasn't cancelled.
    assert stock_of(db, shrimp) + units_in_live_orders(db, shrimp) == 10
    assert stock_of(db, shrimp) >= 0
