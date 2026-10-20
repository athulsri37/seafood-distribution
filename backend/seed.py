"""
Seeds the database with demo users and products so the app is
immediately explorable after setup.

Run with: python seed.py  (inside the backend container/venv), after `alembic upgrade head`.

Each demo account gets a random password, printed once when the account is created.
Nothing is stored in the repository. Lost them? Run `python seed.py --reset-demo-passwords`.
"""
import argparse
import secrets
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.product import Product
from app.models.user import User, UserRole

DEMO_USERS = [
    ("admin@seafoodco.com", "Alex Rivera", "Seafood Co HQ", UserRole.ADMIN),
    ("distributor@seafoodco.com", "Jamie Chen", "Gulf Coast Distribution", UserRole.DISTRIBUTOR),
    ("customer@example.com", "Morgan Lee", "Blue Harbor Restaurant", UserRole.CUSTOMER),
]

DEMO_PRODUCTS = [
    dict(name="Atlantic Salmon Fillet", species="Salmon", sku="SLM-001", unit="lb",
         price_per_unit=14.99, quantity_on_hand=200, reorder_threshold=50, warehouse_location="A1"),
    dict(name="Gulf Shrimp (16/20)", species="Shrimp", sku="SHR-002", unit="lb",
         price_per_unit=11.49, quantity_on_hand=40, reorder_threshold=60, warehouse_location="A2"),
    dict(name="Yellowfin Tuna Loin", species="Tuna", sku="TUN-003", unit="lb",
         price_per_unit=19.99, quantity_on_hand=90, reorder_threshold=30, warehouse_location="B1"),
    dict(name="Live Maine Lobster", species="Lobster", sku="LOB-004", unit="each",
         price_per_unit=24.99, quantity_on_hand=25, reorder_threshold=20, warehouse_location="C1"),
    dict(name="Sea Scallops (U10)", species="Scallop", sku="SCL-005", unit="lb",
         price_per_unit=22.49, quantity_on_hand=15, reorder_threshold=25, warehouse_location="B2"),
]


def seed(db: Session, reset_passwords: bool = False) -> dict[str, Optional[str]]:
    """Create any missing demo users and products.

    Returns each demo email with the password it was just given, or None when the
    account already existed and its password was left alone.
    """
    passwords: dict[str, Optional[str]] = {}
    for email, full_name, company_name, role in DEMO_USERS:
        user = db.query(User).filter(User.email == email).first()
        if user and not reset_passwords:
            passwords[email] = None
            continue
        password = secrets.token_urlsafe(12)
        if user:
            user.hashed_password = hash_password(password)
        else:
            db.add(User(email=email, hashed_password=hash_password(password), full_name=full_name,
                        company_name=company_name, role=role))
        passwords[email] = password

    for product in DEMO_PRODUCTS:
        if not db.query(Product).filter(Product.sku == product["sku"]).first():
            db.add(Product(**product))

    db.commit()
    return passwords


def main() -> None:
    parser = argparse.ArgumentParser(description="Load demo users and products.")
    parser.add_argument("--reset-demo-passwords", action="store_true",
                        help="give the demo accounts new random passwords and print them")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        passwords = seed(db, reset_passwords=args.reset_demo_passwords)
    finally:
        db.close()

    print("Seed data created.")
    new = {email: pw for email, pw in passwords.items() if pw}
    if new:
        print("\nDemo logins (shown only now; save them somewhere safe):")
        for email, password in new.items():
            print(f"  {email:<28} {password}")
    kept = [email for email, pw in passwords.items() if not pw]
    if kept:
        print(f"\nKept existing passwords for {', '.join(kept)}.")
        print("Run `python seed.py --reset-demo-passwords` to replace them.")


if __name__ == "__main__":
    main()
