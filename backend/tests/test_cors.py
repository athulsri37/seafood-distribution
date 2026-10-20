"""Only configured origins may call the API from another site."""
from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import load_settings, settings
from app.main import create_app

PREFLIGHT = {"Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization"}


@pytest.fixture
def client_with_origins(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[str], TestClient]]:
    def _client(origins: str) -> TestClient:
        monkeypatch.setattr(settings, "cors_origins", origins)
        return TestClient(create_app())

    yield _client


def test_no_origin_is_allowed_by_default(client_with_origins: Callable[[str], TestClient]) -> None:
    client = client_with_origins("")

    response = client.options("/api/users", headers={"Origin": "https://evil.example", **PREFLIGHT})

    assert "access-control-allow-origin" not in response.headers


def test_configured_origin_is_allowed_without_credentials(client_with_origins: Callable[[str], TestClient]) -> None:
    client = client_with_origins("https://app.example.com, https://admin.example.com/")

    response = client.options("/api/users", headers={"Origin": "https://admin.example.com", **PREFLIGHT})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://admin.example.com"
    assert "access-control-allow-credentials" not in response.headers


def test_unlisted_origin_is_refused_when_others_are_configured(client_with_origins: Callable[[str], TestClient]) -> None:
    client = client_with_origins("https://app.example.com")

    preflight = client.options("/api/users", headers={"Origin": "https://evil.example", **PREFLIGHT})
    simple = client.get("/api/health", headers={"Origin": "https://evil.example"})

    assert preflight.status_code == 400
    assert "access-control-allow-origin" not in preflight.headers
    assert "access-control-allow-origin" not in simple.headers


def test_same_origin_requests_still_work(client_with_origins: Callable[[str], TestClient]) -> None:
    client = client_with_origins("")

    response = client.get("/api/health")

    assert response.status_code == 200


def test_wildcard_origin_setting_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "*")

    with pytest.raises(RuntimeError, match="CORS_ORIGINS: can't contain"):
        load_settings(env_file=None)
