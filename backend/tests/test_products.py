from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models.product import Product
from app.models.user import User

NEW_PRODUCT = {
    "name": "Atlantic Salmon Fillet",
    "species": "Salmon",
    "sku": "SLM-001",
    "price_per_unit": 14.99,
    "quantity_on_hand": 200,
    "reorder_threshold": 50,
    "warehouse_location": "A1",
}


def test_create_product_returns_product_with_low_stock_flag(
    client: TestClient, distributor: User, auth_headers: Callable[[User], dict[str, str]]
) -> None:
    response = client.post("/api/products", json=NEW_PRODUCT, headers=auth_headers(distributor))

    assert response.status_code == 201
    body = response.json()
    assert body["sku"] == "SLM-001"
    assert body["unit"] == "lb"
    assert body["is_low_stock"] is False


def test_create_product_rejects_duplicate_sku(
    client: TestClient, distributor: User, auth_headers: Callable[[User], dict[str, str]]
) -> None:
    headers = auth_headers(distributor)
    client.post("/api/products", json=NEW_PRODUCT, headers=headers)

    response = client.post("/api/products", json=NEW_PRODUCT, headers=headers)

    assert response.status_code == 400


def test_create_product_rejects_non_positive_price(
    client: TestClient, distributor: User, auth_headers: Callable[[User], dict[str, str]]
) -> None:
    payload = {**NEW_PRODUCT, "price_per_unit": 0}

    response = client.post("/api/products", json=payload, headers=auth_headers(distributor))

    assert response.status_code == 422


def test_update_product_changes_only_sent_fields(
    client: TestClient,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    product = make_product(quantity_on_hand=100, price_per_unit="10.00")

    response = client.patch(
        f"/api/products/{product.id}", json={"quantity_on_hand": 5}, headers=auth_headers(distributor)
    )

    assert response.status_code == 200
    assert response.json()["quantity_on_hand"] == 5
    assert response.json()["price_per_unit"] == 10.0


def test_update_missing_product_returns_404(
    client: TestClient, distributor: User, auth_headers: Callable[[User], dict[str, str]]
) -> None:
    response = client.patch("/api/products/999", json={"quantity_on_hand": 5}, headers=auth_headers(distributor))

    assert response.status_code == 404


def test_low_stock_filter_returns_only_products_at_or_below_threshold(
    client: TestClient,
    customer: User,
    make_product: Callable[..., Product],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    make_product(quantity_on_hand=100, reorder_threshold=20, name="Plenty")
    make_product(quantity_on_hand=20, reorder_threshold=20, name="At threshold")
    make_product(quantity_on_hand=5, reorder_threshold=20, name="Nearly out")

    response = client.get("/api/products", params={"low_stock_only": True}, headers=auth_headers(customer))

    assert response.status_code == 200
    assert sorted(p["name"] for p in response.json()) == ["At threshold", "Nearly out"]


def test_delete_product_removes_it(
    client: TestClient,
    admin: User,
    make_product: Callable[..., Product],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    product = make_product()
    headers = auth_headers(admin)

    response = client.delete(f"/api/products/{product.id}", headers=headers)

    assert response.status_code == 204
    assert client.get("/api/products", headers=headers).json() == []
