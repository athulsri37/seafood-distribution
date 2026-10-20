"""Who may call which endpoint. Business behaviour is covered in the per-resource tests."""
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.models.product import Product
from app.models.user import User, UserRole
from tests.helpers import Headers

NEW_PRODUCT = {"name": "Halibut", "species": "Halibut", "sku": "HAL-001", "price_per_unit": 18.5}
NEW_STAFF = {
    "email": "new.staff@example.com",
    "password": "Staff123!",
    "full_name": "New Staff",
    "role": "DISTRIBUTOR",
}


def call(client: TestClient, action: str, product: Product, headers: dict[str, str]) -> Response:
    if action == "create_product":
        return client.post("/api/products", json=NEW_PRODUCT, headers=headers)
    if action == "update_product":
        return client.patch(f"/api/products/{product.id}", json={"quantity_on_hand": 5}, headers=headers)
    if action == "adjust_stock":
        return client.post(f"/api/products/{product.id}/stock-adjustments", json={"change": 5}, headers=headers)
    if action == "delete_product":
        return client.delete(f"/api/products/{product.id}", headers=headers)
    if action == "update_order_status":
        # Order 999 doesn't exist: allowed roles get 404, forbidden roles are stopped first.
        return client.patch("/api/orders/999/status", json={"status": "CONFIRMED"}, headers=headers)
    if action == "dashboard":
        return client.get("/api/reports/dashboard", headers=headers)
    if action == "list_users":
        return client.get("/api/users", headers=headers)
    if action == "create_user":
        return client.post("/api/users", json=NEW_STAFF, headers=headers)
    if action == "change_user_role":
        # User 999 doesn't exist: admins get 404, everyone else is stopped first.
        return client.patch("/api/users/999/role", json={"role": "DISTRIBUTOR"}, headers=headers)
    raise ValueError(action)


# (action, {role: expected status})
MATRIX = [
    ("create_product", {UserRole.CUSTOMER: 403, UserRole.DISTRIBUTOR: 201, UserRole.ADMIN: 201}),
    ("update_product", {UserRole.CUSTOMER: 403, UserRole.DISTRIBUTOR: 200, UserRole.ADMIN: 200}),
    ("adjust_stock", {UserRole.CUSTOMER: 403, UserRole.DISTRIBUTOR: 200, UserRole.ADMIN: 200}),
    ("delete_product", {UserRole.CUSTOMER: 403, UserRole.DISTRIBUTOR: 403, UserRole.ADMIN: 204}),
    ("update_order_status", {UserRole.CUSTOMER: 403, UserRole.DISTRIBUTOR: 404, UserRole.ADMIN: 404}),
    ("dashboard", {UserRole.CUSTOMER: 403, UserRole.DISTRIBUTOR: 200, UserRole.ADMIN: 200}),
    ("list_users", {UserRole.CUSTOMER: 403, UserRole.DISTRIBUTOR: 403, UserRole.ADMIN: 200}),
    ("create_user", {UserRole.CUSTOMER: 403, UserRole.DISTRIBUTOR: 403, UserRole.ADMIN: 201}),
    ("change_user_role", {UserRole.CUSTOMER: 403, UserRole.DISTRIBUTOR: 403, UserRole.ADMIN: 404}),
]
CASES = [(action, role, status) for action, expected in MATRIX for role, status in expected.items()]


@pytest.mark.parametrize(
    "action, role, expected_status",
    CASES,
    ids=[f"{action}-{role.value.lower()}" for action, role, _ in CASES],
)
def test_role_access(
    client: TestClient,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
    action: str,
    role: UserRole,
    expected_status: int,
) -> None:
    product = make_product()
    user = make_user(role)

    response = call(client, action, product, auth_headers(user))

    assert response.status_code == expected_status


@pytest.mark.parametrize("action", [action for action, _ in MATRIX])
def test_unauthenticated_requests_are_rejected(
    client: TestClient, make_product: Callable[..., Product], action: str
) -> None:
    response = call(client, action, make_product(), headers={})

    assert response.status_code == 401


@pytest.mark.parametrize(
    "method, url",
    [("get", "/api/products"), ("get", "/api/orders"), ("post", "/api/orders")],
)
def test_customer_facing_endpoints_require_login(client: TestClient, method: str, url: str) -> None:
    response = client.request(method, url, json={"items": []} if method == "post" else None)

    assert response.status_code == 401
