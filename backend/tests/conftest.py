"""Shared fixtures for the API test suite.

Tests run against a real PostgreSQL database named by TEST_DATABASE_URL. The suite
refuses to start without it, so it can never touch a development database. The schema
is rebuilt from the Alembic migrations once per run, and every table is emptied after
each test.
"""
import itertools
import os
from collections.abc import Callable, Iterator
from decimal import Decimal

import pytest

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.exit(
        "TEST_DATABASE_URL is not set. Point it at a throwaway PostgreSQL database "
        "(see README, 'Running the tests').",
        returncode=4,
    )
# The app reads its settings at import time, so set them before importing. Both override
# anything in a local backend/.env, so tests never use real credentials.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET_KEY"] = "test-only-jwt-secret-not-used-anywhere-else"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models.product import Product  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from tests.helpers import BACKEND_DIR, DEFAULT_PASSWORD  # noqa: E402


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    return config


@pytest.fixture(scope="session", autouse=True)
def _migrated_database(alembic_config: Config) -> None:
    # Start from an empty schema so the run tests the migrations, not leftovers.
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    command.upgrade(alembic_config, "head")


@pytest.fixture(autouse=True)
def _clean_tables() -> Iterator[None]:
    yield
    # Table names come from our own metadata, not from input.
    tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    counter = itertools.count(1)

    def _make(role: UserRole = UserRole.CUSTOMER, password: str = DEFAULT_PASSWORD) -> User:
        n = next(counter)
        user = User(
            email=f"{role.value.lower()}{n}@example.com",
            hashed_password=hash_password(password),
            full_name=f"{role.value.title()} {n}",
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture
def make_product(db: Session) -> Callable[..., Product]:
    counter = itertools.count(1)

    def _make(
        quantity_on_hand: int = 100,
        price_per_unit: str = "10.00",
        reorder_threshold: int = 20,
        name: str | None = None,
    ) -> Product:
        n = next(counter)
        product = Product(
            name=name or f"Test Fish {n}",
            species="Test",
            sku=f"TST-{n:03d}",
            unit="lb",
            price_per_unit=Decimal(price_per_unit),
            quantity_on_hand=quantity_on_hand,
            reorder_threshold=reorder_threshold,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    return _make


@pytest.fixture
def auth_headers() -> Callable[[User], dict[str, str]]:
    def _headers(user: User) -> dict[str, str]:
        token = create_access_token({"sub": str(user.id), "role": user.role.value})
        return {"Authorization": f"Bearer {token}"}

    return _headers


@pytest.fixture
def admin(make_user: Callable[..., User]) -> User:
    return make_user(UserRole.ADMIN)


@pytest.fixture
def distributor(make_user: Callable[..., User]) -> User:
    return make_user(UserRole.DISTRIBUTOR)


@pytest.fixture
def customer(make_user: Callable[..., User]) -> User:
    return make_user(UserRole.CUSTOMER)
