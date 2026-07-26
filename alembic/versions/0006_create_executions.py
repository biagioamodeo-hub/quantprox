"""Create executions.

Revision ID: 0006_executions
Revises: 0005_decisions
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0006_executions"
down_revision = "0005_decisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "executions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("notional", sa.Numeric(precision=24, scale=8), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_executions_order_id", "executions", ["order_id"], unique=True)
    op.create_index("ix_executions_executed_at", "executions", ["executed_at"])


def downgrade() -> None:
    op.drop_table("executions")
