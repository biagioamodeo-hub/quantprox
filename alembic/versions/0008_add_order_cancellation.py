"""Add order cancellation timestamp.

Revision ID: 0008_order_cancellation
Revises: 0007_realized_pnl
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0008_order_cancellation"
down_revision = "0007_realized_pnl"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "cancelled_at")
