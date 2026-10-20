"""Reading orders takes a fixed number of queries, however many orders or items there are.

Each relationship the response needs is loaded in one batch (selectinload); without that,
every order and item adds its own queries (the N+1 problem).
"""
from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.product import Product
from app.models.user import User, UserRole
from tests.helpers import Headers, capture_queries, place_order


def queries_for(client: TestClient, url: str, headers: dict[str, str]) -> int:
    with capture_queries() as statements:
        response = client.get(url, headers=headers)
    assert response.status_code == 200
    return len(statements)


def test_listing_orders_takes_the_same_queries_for_1_or_20_orders(
    client: TestClient,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    staff = make_user(UserRole.DISTRIBUTOR)
    products = [make_product() for _ in range(3)]

    def add_orders(count: int) -> None:
        for _ in range(count):
            buyer = make_user(UserRole.CUSTOMER)
            place_order(client, auth_headers(buyer), *[(p, 1) for p in products])

    add_orders(1)
    with_one = queries_for(client, "/api/orders", auth_headers(staff))
    add_orders(19)
    with_twenty = queries_for(client, "/api/orders", auth_headers(staff))

    # The user, the orders, then one batch each for customers, items and products.
    assert with_one == with_twenty == 5


def test_getting_an_order_takes_the_same_queries_for_1_or_8_items(
    client: TestClient,
    customer: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    headers = auth_headers(customer)
    small = place_order(client, headers, (make_product(), 1)).json()["id"]
    large = place_order(client, headers, *[(make_product(), 1) for _ in range(8)]).json()["id"]

    assert queries_for(client, f"/api/orders/{small}", headers) == queries_for(client, f"/api/orders/{large}", headers)
