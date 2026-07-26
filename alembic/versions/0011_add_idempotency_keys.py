"""Add idempotency keys to orders and executions.

Revision ID: 0011_idempotency_keys
Revises: 0010_portfolio_tenants
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0011_idempotency_keys"
down_revision = "0010_portfolio_tenants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_name in ("orders", "executions"):
        op.add_column(
            table_name,
            sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        )
        op.add_column(
            table_name,
            sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
        )
    op.create_unique_constraint(
        "uq_order_portfolio_idempotency_key",
        "orders",
        ["portfolio_id", "idempotency_key"],
    )
    op.create_unique_constraint(
        "uq_execution_order_idempotency_key",
        "executions",
        ["order_id", "idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_execution_order_idempotency_key", "executions", type_="unique"
    )
    op.drop_constraint("uq_order_portfolio_idempotency_key", "orders", type_="unique")
    for table_name in ("executions", "orders"):
        op.drop_column(table_name, "request_fingerprint")
        op.drop_column(table_name, "idempotency_key")
