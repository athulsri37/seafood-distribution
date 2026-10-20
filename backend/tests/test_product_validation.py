"""Product create and edit requests are validated before they reach the database.

Bad input must come back as a 422 that names the field, never as a 500 or as bad data saved.
"""
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.user import User
from tests.helpers import Headers

VALID_PRODUCT = {
    "name": "Pacific Halibut",
    "species": "Halibut",
    "sku": "HAL-010",
    "price_per_unit": 18.5,
    "quantity_on_hand": 40,
    "reorder_threshold": 10,
}

INVALID_EDITS = [
    ({"quantity_on_hand": -1}, "quantity_on_hand"),
    ({"quantity_on_hand": 2_147_483_648}, "quantity_on_hand"),  # beyond the INTEGER column
    ({"reorder_threshold": -5}, "reorder_threshold"),
    ({"price_per_unit": 0}, "price_per_unit"),
    ({"price_per_unit": -3.5}, "price_per_unit"),
    ({"price_per_unit": 100_000_000}, "price_per_unit"),  # beyond NUMERIC(10, 2)
    ({"price_per_unit": 0.001}, "price_per_unit"),  # would be stored as 0.00
    ({"name": ""}, "name"),
    ({"name": "   "}, "name"),
    ({"name": None}, "name"),
    ({"price_per_unit": None}, "price_per_unit"),
    ({"quantity_on_hand": None}, "quantity_on_hand"),
    ({"reorder_threshold": None}, "reorder_threshold"),
]


@pytest.mark.parametrize(
    "edit, field", INVALID_EDITS, ids=[f"{f}={list(e.values())[0]!r}" for e, f in INVALID_EDITS]
)
def test_invalid_edit_is_rejected_and_nothing_changes(
    client: TestClient,
    db: Session,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
    edit: dict,
    field: str,
) -> None:
    product = make_product(quantity_on_hand=25, price_per_unit="12.00", reorder_threshold=5, name="Cod Loin")

    response = client.patch(f"/api/products/{product.id}", json=edit, headers=auth_headers(distributor))

    assert response.status_code == 422
    assert field in {str(part) for error in response.json()["detail"] for part in error["loc"]}
    db.refresh(product)
    assert (product.name, product.quantity_on_hand, float(product.price_per_unit), product.reorder_threshold) == (
        "Cod Loin",
        25,
        12.0,
        5,
    )


@pytest.mark.parametrize(
    "edit, expected",
    [
        ({"quantity_on_hand": 0}, {"quantity_on_hand": 0}),
        ({"reorder_threshold": 0}, {"reorder_threshold": 0}),
        ({"price_per_unit": 0.01}, {"price_per_unit": 0.01}),
        ({"name": "  Cod Loin (Skin On)  "}, {"name": "Cod Loin (Skin On)"}),
        ({"warehouse_location": None}, {"warehouse_location": None}),
        ({}, {"quantity_on_hand": 25}),
    ],
    ids=["zero-stock", "zero-threshold", "smallest-price", "name-trimmed", "clear-location", "empty-edit"],
)
def test_valid_edit_is_saved(
    client: TestClient,
    distributor: User,
    make_product: Callable[..., Product],
    auth_headers: Headers,
    edit: dict,
    expected: dict,
) -> None:
    product = make_product(quantity_on_hand=25)

    response = client.patch(f"/api/products/{product.id}", json=edit, headers=auth_headers(distributor))

    assert response.status_code == 200
    assert {key: response.json()[key] for key in expected} == expected


INVALID_CREATES = [
    ({"name": ""}, "name"),
    ({"species": " "}, "species"),
    ({"sku": ""}, "sku"),
    ({"unit": ""}, "unit"),
    ({"price_per_unit": 100_000_000}, "price_per_unit"),
    ({"quantity_on_hand": 2_147_483_648}, "quantity_on_hand"),
    ({"reorder_threshold": -1}, "reorder_threshold"),
]


@pytest.mark.parametrize(
    "change, field", INVALID_CREATES, ids=[f"{f}={list(c.values())[0]!r}" for c, f in INVALID_CREATES]
)
def test_invalid_new_product_is_rejected(
    client: TestClient,
    db: Session,
    distributor: User,
    auth_headers: Headers,
    change: dict,
    field: str,
) -> None:
    response = client.post("/api/products", json={**VALID_PRODUCT, **change}, headers=auth_headers(distributor))

    assert response.status_code == 422
    assert field in {str(part) for error in response.json()["detail"] for part in error["loc"]}
    assert db.query(Product).count() == 0


def test_new_product_text_fields_are_trimmed(
    client: TestClient, distributor: User, auth_headers: Headers
) -> None:
    payload = {**VALID_PRODUCT, "name": "  Pacific Halibut ", "sku": " HAL-010 "}

    response = client.post("/api/products", json=payload, headers=auth_headers(distributor))

    assert response.status_code == 201
    assert (response.json()["name"], response.json()["sku"]) == ("Pacific Halibut", "HAL-010")
