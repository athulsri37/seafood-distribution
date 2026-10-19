"""The Alembic migrations and the SQLAlchemy models must describe the same schema."""
import runpy

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.database import Base, engine
from app.models import Product, User
from tests.helpers import BACKEND_DIR


def test_models_match_migrations() -> None:
    with engine.connect() as conn:
        differences = compare_metadata(MigrationContext.configure(conn), Base.metadata)

    assert differences == [], (
        "The models and migrations differ. Generate a migration with "
        "`alembic revision --autogenerate -m '<change>'` and review it."
    )


def test_migrations_have_a_single_head(alembic_config: Config) -> None:
    heads = ScriptDirectory.from_config(alembic_config).get_heads()

    assert len(heads) == 1, f"Multiple migration heads {heads}; merge them with `alembic merge`."


def test_downgrade_to_base_and_upgrade_again(alembic_config: Config) -> None:
    command.downgrade(alembic_config, "base")
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names()) - {"alembic_version"}
        enum_types = conn.execute(text("SELECT typname FROM pg_type WHERE typtype = 'e'")).scalars().all()

    command.upgrade(alembic_config, "head")

    assert tables == set()
    assert enum_types == []
    with engine.connect() as conn:
        assert set(inspect(conn).get_table_names()) >= {"users", "products", "orders", "order_items"}


def test_seed_script_loads_demo_data_once(db: Session) -> None:
    seed_script = str(BACKEND_DIR / "seed.py")

    runpy.run_path(seed_script)
    runpy.run_path(seed_script)  # A second run must not duplicate anything.

    assert db.query(User).count() == 3
    assert db.query(Product).count() == 5
