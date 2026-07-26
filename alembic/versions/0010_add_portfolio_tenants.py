"""Add tenant ownership to portfolios.

Revision ID: 0010_portfolio_tenants
Revises: 0009_partial_fills
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0010_portfolio_tenants"
down_revision = "0009_partial_fills"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "portfolios",
        sa.Column(
            "tenant_id",
            sa.String(length=64),
            nullable=False,
            server_default="demo",
        ),
    )
    op.drop_index("ix_portfolios_name", table_name="portfolios")
    op.create_index("ix_portfolios_name", "portfolios", ["name"], unique=False)
    op.create_index(
        "ix_portfolios_tenant_id", "portfolios", ["tenant_id"], unique=False
    )
    op.create_unique_constraint(
        "uq_portfolio_tenant_name", "portfolios", ["tenant_id", "name"]
    )
    op.alter_column("portfolios", "tenant_id", server_default=None)


def downgrade() -> None:
    op.drop_constraint("uq_portfolio_tenant_name", "portfolios", type_="unique")
    op.drop_index("ix_portfolios_tenant_id", table_name="portfolios")
    op.drop_index("ix_portfolios_name", table_name="portfolios")
    op.create_index("ix_portfolios_name", "portfolios", ["name"], unique=True)
    op.drop_column("portfolios", "tenant_id")
