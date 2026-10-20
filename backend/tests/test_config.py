"""The backend refuses to start without real credentials, and says what to fix."""
import pytest

from app.core.config import load_settings

VALID_SECRET = "test-only-" + "s" * 40
DATABASE_URL = "postgresql://seafood:test-only@localhost:5432/seafood_distribution"


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # conftest sets both for the app under test; each case here starts without them.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)


def test_missing_settings_are_all_named(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(RuntimeError) as error:
        load_settings(env_file=None)

    message = str(error.value)
    assert "DATABASE_URL: not set" in message
    assert "JWT_SECRET_KEY: not set" in message
    assert "backend/.env.example" in message
    assert "secrets.token_urlsafe" in message


@pytest.mark.parametrize(
    "secret, reason",
    [
        ("change_this_secret_in_production", "published on GitHub"),
        ("too-short", "at least 32 characters"),
        ("", "at least 32 characters"),
    ],
    ids=["published-default", "too-short", "empty"],
)
def test_weak_jwt_secrets_are_refused(monkeypatch: pytest.MonkeyPatch, secret: str, reason: str) -> None:
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", secret)

    with pytest.raises(RuntimeError, match=reason):
        load_settings(env_file=None)


def test_complete_settings_load(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", VALID_SECRET)

    settings = load_settings(env_file=None)

    assert settings.database_url == DATABASE_URL
    assert settings.jwt_secret_key == VALID_SECRET
    assert settings.access_token_expire_minutes == 60


def test_settings_can_come_from_an_env_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(f"DATABASE_URL={DATABASE_URL}\nJWT_SECRET_KEY={VALID_SECRET}\n", encoding="utf-8")

    settings = load_settings(env_file=str(env_file))

    assert settings.jwt_secret_key == VALID_SECRET
