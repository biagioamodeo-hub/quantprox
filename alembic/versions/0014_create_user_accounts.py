"""Create persistent user accounts.

Revision ID: 0014_user_accounts
Revises: 0013_broker_submissions
Create Date: 2026-07-27
"""

import sqlalchemy as sa

from alembic import op

revision = "0014_user_accounts"
down_revision = "0013_broker_submissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile", sa.String(length=32), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("phone", sa.String(length=24), nullable=True),
        sa.Column("preferred_currency", sa.String(length=3), nullable=False),
        sa.Column("password_hash", sa.String(length=64), nullable=False),
        sa.Column("password_salt", sa.String(length=32), nullable=False),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_accounts_profile", "user_accounts", ["profile"], unique=True
    )
    op.create_index("ix_user_accounts_email", "user_accounts", ["email"], unique=True)


def downgrade() -> None:
    op.drop_table("user_accounts")
