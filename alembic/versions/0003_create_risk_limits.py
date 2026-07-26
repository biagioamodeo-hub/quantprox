"""Create risk limits.

Revision ID: 0003_risk_limits
Revises: 0002_portfolio
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_risk_limits"
down_revision = "0002_portfolio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_limits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column(
            "max_order_notional", sa.Numeric(precision=24, scale=8), nullable=False
        ),
        sa.Column(
            "max_total_exposure", sa.Numeric(precision=24, scale=8), nullable=False
        ),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_risk_limits_portfolio_id",
        "risk_limits",
        ["portfolio_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("risk_limits")
