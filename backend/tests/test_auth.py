import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.helpers import DEFAULT_PASSWORD, Headers

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/auth/me"


def registration(**overrides: str) -> dict[str, str]:
    payload = {
        "email": "buyer@example.com",
        "password": "Secret123!",
        "full_name": "Morgan Lee",
        "company_name": "Blue Harbor Restaurant",
    }
    payload.update(overrides)
    return payload


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_creates_customer_and_returns_token(client: TestClient) -> None:
    response = client.post(REGISTER_URL, json=registration())

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["role"] == "CUSTOMER"
    assert "hashed_password" not in body["user"]


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    client.post(REGISTER_URL, json=registration())

    response = client.post(REGISTER_URL, json=registration())

    assert response.status_code == 400


def test_register_rejects_invalid_email(client: TestClient) -> None:
    response = client.post(REGISTER_URL, json=registration(email="not-an-email"))

    assert response.status_code == 422


@pytest.mark.xfail(reason="B1: self-registration accepts any role, including ADMIN")
def test_self_registration_cannot_create_admin(client: TestClient) -> None:
    response = client.post(REGISTER_URL, json=registration(role="ADMIN"))

    if response.status_code == 201:
        assert response.json()["user"]["role"] == "CUSTOMER"
    else:
        assert response.status_code in (403, 422)


def test_login_returns_token_for_correct_password(
    client: TestClient, customer: User
) -> None:
    response = client.post(LOGIN_URL, json={"email": customer.email, "password": DEFAULT_PASSWORD})

    assert response.status_code == 200
    assert response.json()["user"]["id"] == customer.id


@pytest.mark.parametrize("wrong_field", ["password", "email"])
def test_login_rejects_bad_credentials(client: TestClient, customer: User, wrong_field: str) -> None:
    credentials = {"email": customer.email, "password": DEFAULT_PASSWORD}
    credentials[wrong_field] = "nobody@example.com" if wrong_field == "email" else "wrong-password"

    response = client.post(LOGIN_URL, json=credentials)

    assert response.status_code == 401


def test_me_returns_current_user(
    client: TestClient, customer: User, auth_headers: Headers
) -> None:
    response = client.get(ME_URL, headers=auth_headers(customer))

    assert response.status_code == 200
    assert response.json()["email"] == customer.email


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer not-a-real-token"}],
    ids=["no-token", "garbage-token"],
)
def test_me_rejects_missing_or_invalid_token(client: TestClient, headers: dict[str, str]) -> None:
    response = client.get(ME_URL, headers=headers)

    assert response.status_code == 401


def test_me_rejects_token_for_deleted_user(
    client: TestClient, customer: User, auth_headers: Headers, db: Session
) -> None:
    headers = auth_headers(customer)
    db.delete(customer)
    db.commit()

    response = client.get(ME_URL, headers=headers)

    assert response.status_code == 401
