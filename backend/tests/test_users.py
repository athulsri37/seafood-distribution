from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from tests.helpers import Headers

NEW_ACCOUNT = {
    "email": "jamie.chen@example.com",
    "password": "Test-only-pw-1",
    "full_name": "Jamie Chen",
    "company_name": "Gulf Coast Distribution",
}


@pytest.mark.parametrize("role", ["ADMIN", "DISTRIBUTOR", "CUSTOMER"])
def test_admin_creates_account_with_any_role(
    client: TestClient, admin: User, auth_headers: Headers, role: str
) -> None:
    response = client.post("/api/users", json={**NEW_ACCOUNT, "role": role}, headers=auth_headers(admin))

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == role
    assert body["email"] == NEW_ACCOUNT["email"]
    assert "hashed_password" not in body


def test_account_created_by_admin_can_log_in(client: TestClient, admin: User, auth_headers: Headers) -> None:
    client.post("/api/users", json={**NEW_ACCOUNT, "role": "DISTRIBUTOR"}, headers=auth_headers(admin))

    response = client.post(
        "/api/auth/login", json={"email": NEW_ACCOUNT["email"], "password": NEW_ACCOUNT["password"]}
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "DISTRIBUTOR"


def test_admin_cannot_create_account_with_existing_email(
    client: TestClient, admin: User, customer: User, auth_headers: Headers
) -> None:
    payload = {**NEW_ACCOUNT, "email": customer.email, "role": "DISTRIBUTOR"}

    response = client.post("/api/users", json=payload, headers=auth_headers(admin))

    assert response.status_code == 400


def test_admin_must_choose_a_role(client: TestClient, admin: User, auth_headers: Headers) -> None:
    response = client.post("/api/users", json=NEW_ACCOUNT, headers=auth_headers(admin))

    assert response.status_code == 422


def test_admin_promotes_customer_to_distributor(
    client: TestClient, db: Session, admin: User, customer: User, auth_headers: Headers
) -> None:
    response = client.patch(
        f"/api/users/{customer.id}/role", json={"role": "DISTRIBUTOR"}, headers=auth_headers(admin)
    )

    assert response.status_code == 200
    assert response.json()["role"] == "DISTRIBUTOR"
    db.refresh(customer)
    assert customer.role == UserRole.DISTRIBUTOR


def test_promoted_user_gets_new_permissions_with_existing_token(
    client: TestClient, admin: User, customer: User, auth_headers: Headers
) -> None:
    customer_headers = auth_headers(customer)
    assert client.get("/api/reports/dashboard", headers=customer_headers).status_code == 403

    client.patch(f"/api/users/{customer.id}/role", json={"role": "DISTRIBUTOR"}, headers=auth_headers(admin))

    # The role is read from the database on every request, not from the token.
    assert client.get("/api/reports/dashboard", headers=customer_headers).status_code == 200


def test_admin_can_demote_another_admin(
    client: TestClient, make_user: Callable[..., User], auth_headers: Headers
) -> None:
    acting_admin, other_admin = make_user(UserRole.ADMIN), make_user(UserRole.ADMIN)

    response = client.patch(
        f"/api/users/{other_admin.id}/role", json={"role": "DISTRIBUTOR"}, headers=auth_headers(acting_admin)
    )

    assert response.status_code == 200
    assert response.json()["role"] == "DISTRIBUTOR"


@pytest.mark.parametrize("role", ["DISTRIBUTOR", "CUSTOMER"])
def test_admin_cannot_remove_own_admin_role(
    client: TestClient, db: Session, admin: User, auth_headers: Headers, role: str
) -> None:
    response = client.patch(f"/api/users/{admin.id}/role", json={"role": role}, headers=auth_headers(admin))

    assert response.status_code == 400
    assert "your own admin role" in response.json()["detail"]
    db.refresh(admin)
    assert admin.role == UserRole.ADMIN


def test_admin_setting_own_role_to_admin_is_allowed(
    client: TestClient, admin: User, auth_headers: Headers
) -> None:
    response = client.patch(f"/api/users/{admin.id}/role", json={"role": "ADMIN"}, headers=auth_headers(admin))

    assert response.status_code == 200


def test_unknown_role_is_rejected(client: TestClient, admin: User, customer: User, auth_headers: Headers) -> None:
    response = client.patch(
        f"/api/users/{customer.id}/role", json={"role": "SUPERUSER"}, headers=auth_headers(admin)
    )

    assert response.status_code == 422
