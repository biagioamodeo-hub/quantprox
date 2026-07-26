"""Create decisions.

Revision ID: 0005_decisions
Revises: 0004_orders
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0005_decisions"
down_revision = "0004_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "decisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("short_window", sa.Integer(), nullable=False),
        sa.Column("long_window", sa.Integer(), nullable=False),
        sa.Column("short_average", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("long_average", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("action", sa.String(length=4), nullable=False),
        sa.Column("rationale", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decisions_portfolio_id", "decisions", ["portfolio_id"])
    op.create_index("ix_decisions_instrument_id", "decisions", ["instrument_id"])
    op.create_index("ix_decisions_action", "decisions", ["action"])
    op.create_index("ix_decisions_created_at", "decisions", ["created_at"])


def downgrade() -> None:
    op.drop_table("decisions")
