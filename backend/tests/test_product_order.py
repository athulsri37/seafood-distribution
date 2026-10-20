"""The product list has a fixed order, so it doesn't reshuffle when stock changes."""
from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.product import Product
from app.models.user import User
from tests.helpers import Headers


def names(client: TestClient, headers: dict[str, str], **params) -> list[str]:
    return [p["name"] for p in client.get("/api/products", params=params, headers=headers).json()]


def test_products_are_listed_alphabetically_and_stay_put_after_a_stock_change(
    client: TestClient,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    headers = auth_headers(distributor)
    created = {name: make_product(name=name) for name in ["Tuna", "abalone", "Salmon", "Cod"]}

    before = names(client, headers)
    client.post(f"/api/products/{created['Cod'].id}/stock-adjustments", json={"change": 5}, headers=headers)
    client.patch(f"/api/products/{created['abalone'].id}", json={"price_per_unit": 30}, headers=headers)
    after = names(client, headers)

    assert before == ["abalone", "Cod", "Salmon", "Tuna"]
    assert after == before


def test_low_stock_list_uses_the_same_order(
    client: TestClient, customer: User, make_product: Callable[..., Product], auth_headers: Headers
) -> None:
    for name in ["Scallops", "Lobster", "Mussels"]:
        make_product(name=name, quantity_on_hand=1, reorder_threshold=10)

    assert names(client, auth_headers(customer), low_stock_only=True) == ["Lobster", "Mussels", "Scallops"]


def test_products_with_the_same_name_keep_a_stable_order(
    client: TestClient, customer: User, make_product: Callable[..., Product], auth_headers: Headers
) -> None:
    first, second = make_product(name="Oysters"), make_product(name="Oysters")

    ids = [p["id"] for p in client.get("/api/products", headers=auth_headers(customer)).json()]

    assert ids == [first.id, second.id]
