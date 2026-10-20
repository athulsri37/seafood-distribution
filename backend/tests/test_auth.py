import pytest
from fastapi.testclient import TestClient
from jose import jwt
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


@pytest.mark.parametrize("role", ["ADMIN", "DISTRIBUTOR"])
def test_self_registration_cannot_create_staff_account(
    client: TestClient, db: Session, role: str
) -> None:
    response = client.post(REGISTER_URL, json=registration(role=role))

    assert response.status_code == 403
    assert "customer accounts only" in response.json()["detail"]
    assert db.query(User).count() == 0


def test_self_registration_accepts_explicit_customer_role(client: TestClient) -> None:
    response = client.post(REGISTER_URL, json=registration(role="CUSTOMER"))

    assert response.status_code == 201
    assert response.json()["user"]["role"] == "CUSTOMER"


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


def test_token_signed_with_the_old_published_secret_is_rejected(client: TestClient, admin: User) -> None:
    # Before B2, a missing JWT_SECRET_KEY fell back to a secret published in this repo,
    # so anyone could forge an admin token like this one.
    forged = jwt.encode({"sub": str(admin.id), "role": "ADMIN"}, "change_this_secret_in_production", algorithm="HS256")

    response = client.get("/api/users", headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


def swagger_token_url(client: TestClient) -> str:
    """Where Swagger UI's Authorize button sends the username and password."""
    schemes = client.get("/openapi.json").json()["components"]["securitySchemes"]
    return schemes["OAuth2PasswordBearer"]["flows"]["password"]["tokenUrl"]


def test_swagger_authorize_gets_a_token_that_works(client: TestClient, customer: User) -> None:
    response = client.post(
        swagger_token_url(client), data={"username": customer.email, "password": DEFAULT_PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    me = client.get(ME_URL, headers={"Authorization": f"Bearer {response.json()['access_token']}"})
    assert me.json()["id"] == customer.id


def test_swagger_authorize_rejects_a_wrong_password(client: TestClient, customer: User) -> None:
    response = client.post(swagger_token_url(client), data={"username": customer.email, "password": "wrong-password"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
