"""Drop the duplicate indexes on primary keys.

Each table had an extra non-unique index on `id` (from `index=True` on the column) next
to the primary key's own index, so every insert maintained two identical indexes.

Revision ID: 31c79a30bbc5
Revises: 91a08277775a
Create Date: 2026-10-20 17:30:13.910214

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '31c79a30bbc5'
down_revision: Union[str, None] = '91a08277775a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = ("users", "products", "orders", "order_items")


def upgrade() -> None:
    for table in TABLES:
        op.drop_index(op.f(f"ix_{table}_id"), table_name=table)


def downgrade() -> None:
    for table in TABLES:
        op.create_index(op.f(f"ix_{table}_id"), table, ["id"], unique=False)
