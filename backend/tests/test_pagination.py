"""Orders and users are paged newest first with a cursor; products are capped."""
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.models.product import Product
from app.models.user import User, UserRole
from tests.helpers import Headers, place_order


def page(client: TestClient, url: str, headers: dict[str, str], **params) -> tuple[list[int], int]:
    response = client.get(url, params=params, headers=headers)
    assert response.status_code == 200
    return [item["id"] for item in response.json()], int(response.headers["X-Total-Count"])


@pytest.fixture
def seven_orders(
    client: TestClient, customer: User, make_product: Callable[..., Product], auth_headers: Headers
) -> list[int]:
    product = make_product(quantity_on_hand=1000)
    return [place_order(client, auth_headers(customer), (product, 1)).json()["id"] for _ in range(7)]


def test_pages_walk_orders_newest_first_without_gaps_or_overlaps(
    client: TestClient, distributor: User, auth_headers: Headers, seven_orders: list[int]
) -> None:
    headers = auth_headers(distributor)

    first, total = page(client, "/api/orders", headers, limit=3)
    second, _ = page(client, "/api/orders", headers, limit=3, before_id=first[-1])
    third, _ = page(client, "/api/orders", headers, limit=3, before_id=second[-1])
    after_last, _ = page(client, "/api/orders", headers, limit=3, before_id=third[-1])

    assert total == 7
    assert first + second + third == sorted(seven_orders, reverse=True)
    assert len(third) == 1
    assert after_last == []


def test_new_order_between_pages_does_not_shift_the_next_page(
    client: TestClient,
    customer: User,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
    seven_orders: list[int],
) -> None:
    headers = auth_headers(distributor)
    first, _ = page(client, "/api/orders", headers, limit=3)

    newest = place_order(client, auth_headers(customer), (make_product(), 1)).json()["id"]
    second, total = page(client, "/api/orders", headers, limit=3, before_id=first[-1])

    assert set(first).isdisjoint(second)
    assert second == sorted(seven_orders, reverse=True)[3:6]
    assert newest not in second
    assert total == 8


def test_default_page_is_50_orders(
    client: TestClient,
    customer: User,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    product = make_product(quantity_on_hand=1000)
    for _ in range(55):
        place_order(client, auth_headers(customer), (product, 1))

    ids, total = page(client, "/api/orders", auth_headers(distributor))

    assert (len(ids), total) == (50, 55)


def test_customer_pages_only_through_their_own_orders(
    client: TestClient,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
    seven_orders: list[int],
) -> None:
    other = make_user(UserRole.CUSTOMER)
    own = [place_order(client, auth_headers(other), (make_product(), 1)).json()["id"] for _ in range(2)]

    ids, total = page(client, "/api/orders", auth_headers(other), limit=50)

    assert (sorted(ids), total) == (sorted(own), 2)


@pytest.mark.parametrize(
    "params", [{"limit": 0}, {"limit": 101}, {"before_id": 0}, {"limit": "many"}], ids=["zero", "over-100", "bad-cursor", "not-a-number"]
)
def test_invalid_paging_parameters_are_rejected(
    client: TestClient, admin: User, auth_headers: Headers, params: dict
) -> None:
    for url in ("/api/orders", "/api/users"):
        assert client.get(url, params=params, headers=auth_headers(admin)).status_code == 422


def test_users_are_paged_newest_first(
    client: TestClient, admin: User, make_user: Callable[..., User], auth_headers: Headers
) -> None:
    created = [admin.id] + [make_user(UserRole.CUSTOMER).id for _ in range(4)]
    headers = auth_headers(admin)

    first, total = page(client, "/api/users", headers, limit=2)
    rest, _ = page(client, "/api/users", headers, limit=10, before_id=first[-1])

    assert total == 5
    assert first + rest == sorted(created, reverse=True)


def test_products_report_their_total_and_cap_the_list(
    client: TestClient, customer: User, make_product: Callable[..., Product], auth_headers: Headers
) -> None:
    for _ in range(3):
        make_product()
    headers = auth_headers(customer)

    ids, total = page(client, "/api/products", headers)
    capped, _ = page(client, "/api/products", headers, limit=2)

    assert (len(ids), total) == (3, 3)
    assert len(capped) == 2
    assert client.get("/api/products", params={"limit": 501}, headers=headers).status_code == 422
