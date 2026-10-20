"""The seed script creates demo data with random passwords that are never stored in the repo."""
import runpy
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Product, User
from seed import DEMO_USERS, seed
from tests.helpers import BACKEND_DIR

DEMO_EMAILS = [email for email, *_ in DEMO_USERS]


def log_in(client: TestClient, email: str, password: str) -> int:
    return client.post("/api/auth/login", json={"email": email, "password": password}).status_code


def test_seed_creates_demo_users_with_working_random_passwords(client: TestClient, db: Session) -> None:
    passwords = seed(db)

    assert list(passwords) == DEMO_EMAILS
    assert all(len(password) >= 16 for password in passwords.values())
    assert len(set(passwords.values())) == len(passwords)
    for email, password in passwords.items():
        assert log_in(client, email, password) == 200
    assert db.query(Product).count() == 5


def test_each_fresh_setup_gets_different_passwords(db: Session) -> None:
    first = seed(db)
    db.query(User).delete()
    db.commit()

    second = seed(db)

    assert all(first[email] != second[email] for email in DEMO_EMAILS)


def test_running_again_keeps_existing_passwords_and_data(client: TestClient, db: Session) -> None:
    original = seed(db)

    again = seed(db)

    assert again == {email: None for email in DEMO_EMAILS}
    assert db.query(User).count() == 3
    assert db.query(Product).count() == 5
    assert log_in(client, DEMO_EMAILS[0], original[DEMO_EMAILS[0]]) == 200


def test_reset_replaces_every_demo_password(client: TestClient, db: Session) -> None:
    original = seed(db)

    reset = seed(db, reset_passwords=True)

    for email in DEMO_EMAILS:
        assert log_in(client, email, original[email]) == 401
        assert log_in(client, email, reset[email]) == 200
    assert db.query(User).count() == 3


def test_script_prints_new_logins_once(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    script = str(BACKEND_DIR / "seed.py")
    monkeypatch.setattr(sys, "argv", ["seed.py"])

    runpy.run_path(script, run_name="__main__")
    first = capsys.readouterr().out
    runpy.run_path(script, run_name="__main__")
    second = capsys.readouterr().out

    assert "Demo logins (shown only now" in first
    assert all(email in first for email in DEMO_EMAILS)
    assert "Demo logins" not in second
    assert "--reset-demo-passwords" in second
