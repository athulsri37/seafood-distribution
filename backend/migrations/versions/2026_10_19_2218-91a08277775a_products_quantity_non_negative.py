"""Stock can never go below zero.

Adds a CHECK constraint on products.quantity_on_hand. It refuses to run while any
product already has negative stock, rather than silently changing the data.

Revision ID: 91a08277775a
Revises: 9974bc68bdcd
Create Date: 2026-10-19 22:18:52.259102

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91a08277775a'
down_revision: Union[str, None] = '9974bc68bdcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CONSTRAINT = "products_quantity_on_hand_non_negative_check"


def upgrade() -> None:
    negative = op.get_bind().execute(
        sa.text("SELECT sku, quantity_on_hand FROM products WHERE quantity_on_hand < 0 ORDER BY sku")
    ).all()
    if negative:
        listed = ", ".join(f"{sku} ({quantity})" for sku, quantity in negative)
        raise RuntimeError(
            f"These products have negative stock: {listed}. "
            "Correct their quantity_on_hand, then run the migration again."
        )
    op.create_check_constraint(op.f(CONSTRAINT), "products", "quantity_on_hand >= 0")


def downgrade() -> None:
    op.drop_constraint(op.f(CONSTRAINT), "products", type_="check")
