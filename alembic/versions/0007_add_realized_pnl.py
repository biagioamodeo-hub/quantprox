"""Add realized P&L to positions.

Revision ID: 0007_realized_pnl
Revises: 0006_executions
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0007_realized_pnl"
down_revision = "0006_executions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "positions",
        sa.Column(
            "realized_pnl",
            sa.Numeric(precision=24, scale=8),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("positions", "realized_pnl")
