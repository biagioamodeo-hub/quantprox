"""Create orders.

Revision ID: 0004_orders
Revises: 0003_risk_limits
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0004_orders"
down_revision = "0003_risk_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("side", sa.String(length=4), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("limit_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("rejection_reason", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_portfolio_id", "orders", ["portfolio_id"])
    op.create_index("ix_orders_instrument_id", "orders", ["instrument_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])


def downgrade() -> None:
    op.drop_table("orders")
