"""
Seeds the database with demo users and products so the app is
immediately explorable after setup.

Run with: python -m seed  (inside the backend container/venv)
"""
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.product import Product

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if not db.query(User).filter(User.email == "admin@seafoodco.com").first():
    db.add_all([
        User(
            email="admin@seafoodco.com",
            hashed_password=hash_password("Admin123!"),
            full_name="Alex Rivera",
            company_name="Seafood Co HQ",
            role=UserRole.ADMIN,
        ),
        User(
            email="distributor@seafoodco.com",
            hashed_password=hash_password("Distributor123!"),
            full_name="Jamie Chen",
            company_name="Gulf Coast Distribution",
            role=UserRole.DISTRIBUTOR,
        ),
        User(
            email="customer@example.com",
            hashed_password=hash_password("Customer123!"),
            full_name="Morgan Lee",
            company_name="Blue Harbor Restaurant",
            role=UserRole.CUSTOMER,
        ),
    ])

if not db.query(Product).filter(Product.sku == "SLM-001").first():
    db.add_all([
        Product(name="Atlantic Salmon Fillet", species="Salmon", sku="SLM-001",
                unit="lb", price_per_unit=14.99, quantity_on_hand=200, reorder_threshold=50,
                warehouse_location="A1"),
        Product(name="Gulf Shrimp (16/20)", species="Shrimp", sku="SHR-002",
                unit="lb", price_per_unit=11.49, quantity_on_hand=40, reorder_threshold=60,
                warehouse_location="A2"),
        Product(name="Yellowfin Tuna Loin", species="Tuna", sku="TUN-003",
                unit="lb", price_per_unit=19.99, quantity_on_hand=90, reorder_threshold=30,
                warehouse_location="B1"),
        Product(name="Live Maine Lobster", species="Lobster", sku="LOB-004",
                unit="each", price_per_unit=24.99, quantity_on_hand=25, reorder_threshold=20,
                warehouse_location="C1"),
        Product(name="Sea Scallops (U10)", species="Scallop", sku="SCL-005",
                unit="lb", price_per_unit=22.49, quantity_on_hand=15, reorder_threshold=25,
                warehouse_location="B2"),
    ])

db.commit()
db.close()
print("Seed data created.")
