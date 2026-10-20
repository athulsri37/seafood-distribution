"""Small helpers shared by test modules. Fixtures live in conftest.py."""
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

from fastapi.testclient import TestClient
from httpx import Response

from app.main import app
from app.models.product import Product
from app.models.user import User

DEFAULT_PASSWORD = "Passw0rd!"

BACKEND_DIR = Path(__file__).resolve().parent.parent

Headers = Callable[[User], dict[str, str]]
Request = tuple[str, str, dict[str, str], dict]  # method, url, headers, json body


def place_order(client: TestClient, headers: dict[str, str], *lines: tuple[Product, int]) -> Response:
    items = [{"product_id": product.id, "quantity": quantity} for product, quantity in lines]
    return client.post("/api/orders", json={"items": items}, headers=headers)


def send_simultaneously(requests: list[Request]) -> list[int]:
    """Send every request at the same moment and return the status codes in order.

    Each request runs in its own thread with its own client, so the API handles them
    concurrently against PostgreSQL, the way simultaneous users would.
    """
    barrier = Barrier(len(requests))

    def send(request: Request) -> int:
        method, url, headers, body = request
        with TestClient(app) as client:
            barrier.wait()
            return client.request(method, url, headers=headers, json=body).status_code

    with ThreadPoolExecutor(max_workers=len(requests)) as pool:
        return list(pool.map(send, requests))
