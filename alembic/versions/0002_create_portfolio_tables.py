"""Create portfolio tables.

Revision ID: 0002_portfolio
Revises: 0001_market_data
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_portfolio"
down_revision = "0001_market_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("cash_balance", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolios_name", "portfolios", ["name"], unique=True)
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("instrument_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("average_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "portfolio_id", "instrument_id", name="uq_position_instrument"
        ),
    )
    op.create_index("ix_positions_portfolio_id", "positions", ["portfolio_id"])
    op.create_index("ix_positions_instrument_id", "positions", ["instrument_id"])


def downgrade() -> None:
    op.drop_table("positions")
    op.drop_table("portfolios")
