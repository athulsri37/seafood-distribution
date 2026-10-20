"""Stock adjustments send the change, not the new total, so simultaneous ones add up."""
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.product import MAX_COUNT
from tests.helpers import Headers, send_simultaneously


def adjust(client: TestClient, headers: dict[str, str], product: Product, change: int):
    return client.post(f"/api/products/{product.id}/stock-adjustments", json={"change": change}, headers=headers)


def stock_of(db: Session, product: Product) -> int:
    db.refresh(product)
    return product.quantity_on_hand


@pytest.mark.parametrize("change, expected", [(10, 110), (-10, 90), (-100, 0)], ids=["add", "remove", "remove-all"])
def test_adjustment_changes_stock_by_the_amount_sent(
    client: TestClient,
    db: Session,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
    change: int,
    expected: int,
) -> None:
    product = make_product(quantity_on_hand=100)

    response = adjust(client, auth_headers(distributor), product, change)

    assert response.status_code == 200
    assert response.json()["quantity_on_hand"] == expected
    assert stock_of(db, product) == expected


def test_removing_more_than_is_in_stock_is_refused(
    client: TestClient,
    db: Session,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    product = make_product(quantity_on_hand=5, name="Sea Scallops")

    response = adjust(client, auth_headers(distributor), product, -10)

    assert response.status_code == 409
    assert response.json()["detail"] == "Can't remove 10 lb: only 5 lb of Sea Scallops in stock."
    assert stock_of(db, product) == 5


def test_adding_beyond_the_column_limit_is_refused(
    client: TestClient,
    db: Session,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    product = make_product(quantity_on_hand=MAX_COUNT - 5)

    response = adjust(client, auth_headers(distributor), product, MAX_COUNT)

    assert response.status_code == 409
    assert stock_of(db, product) == MAX_COUNT - 5


@pytest.mark.parametrize("change", [0, MAX_COUNT + 1, -(MAX_COUNT + 1)], ids=["zero", "too-big", "too-small"])
def test_invalid_change_is_rejected(
    client: TestClient,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
    change: int,
) -> None:
    response = adjust(client, auth_headers(distributor), make_product(), change)

    assert response.status_code == 422


def test_adjusting_unknown_product_returns_404(
    client: TestClient, distributor: User, auth_headers: Headers
) -> None:
    response = client.post("/api/products/999/stock-adjustments", json={"change": 5}, headers=auth_headers(distributor))

    assert response.status_code == 404


def test_simultaneous_additions_all_count(
    db: Session,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    salmon = make_product(quantity_on_hand=200)
    staff = [make_user(UserRole.DISTRIBUTOR) for _ in range(12)]
    url = f"/api/products/{salmon.id}/stock-adjustments"

    statuses = send_simultaneously([("POST", url, auth_headers(s), {"change": 10}) for s in staff])

    assert statuses == [200] * 12
    assert stock_of(db, salmon) == 320


def test_simultaneous_removals_never_take_stock_below_zero(
    db: Session,
    make_user: Callable[..., User],
    make_product: Callable[..., Product],
    auth_headers: Headers,
) -> None:
    shrimp = make_product(quantity_on_hand=50)
    staff = [make_user(UserRole.DISTRIBUTOR) for _ in range(12)]
    url = f"/api/products/{shrimp.id}/stock-adjustments"

    statuses = send_simultaneously([("POST", url, auth_headers(s), {"change": -10}) for s in staff])

    assert statuses.count(200) == 5
    assert statuses.count(409) == 7
    assert stock_of(db, shrimp) == 0
