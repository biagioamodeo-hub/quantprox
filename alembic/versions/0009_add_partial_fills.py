"""Add partial fill support.

Revision ID: 0009_partial_fills
Revises: 0008_order_cancellation
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0009_partial_fills"
down_revision = "0008_order_cancellation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "filled_quantity",
            sa.Numeric(precision=24, scale=8),
            nullable=False,
            server_default="0",
        ),
    )
    op.execute("UPDATE orders SET filled_quantity = quantity WHERE status = 'filled'")
    op.drop_index("ix_executions_order_id", table_name="executions")
    op.create_index("ix_executions_order_id", "executions", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_executions_order_id", table_name="executions")
    op.create_index("ix_executions_order_id", "executions", ["order_id"], unique=True)
    op.drop_column("orders", "filled_quantity")
