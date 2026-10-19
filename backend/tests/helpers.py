"""Small helpers shared by test modules. Fixtures live in conftest.py."""
from collections.abc import Callable
from pathlib import Path

from fastapi.testclient import TestClient
from httpx import Response

from app.models.product import Product
from app.models.user import User

DEFAULT_PASSWORD = "Passw0rd!"

BACKEND_DIR = Path(__file__).resolve().parent.parent

Headers = Callable[[User], dict[str, str]]


def place_order(client: TestClient, headers: dict[str, str], *lines: tuple[Product, int]) -> Response:
    items = [{"product_id": product.id, "quantity": quantity} for product, quantity in lines]
    return client.post("/api/orders", json={"items": items}, headers=headers)
