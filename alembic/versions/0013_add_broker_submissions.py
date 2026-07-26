"""Add broker submissions.

Revision ID: 0013_broker_submissions
Revises: 0012_background_jobs
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0013_broker_submissions"
down_revision = "0012_background_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("external_order_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
        sa.UniqueConstraint(
            "provider",
            "external_order_id",
            name="uq_broker_submission_external_order",
        ),
    )
    op.create_index(
        "ix_broker_submissions_order_id",
        "broker_submissions",
        ["order_id"],
        unique=True,
    )
    op.create_index(
        "ix_broker_submissions_provider",
        "broker_submissions",
        ["provider"],
    )
    op.create_index(
        "ix_broker_submissions_status",
        "broker_submissions",
        ["status"],
    )
    op.create_index(
        "ix_broker_submissions_submitted_at",
        "broker_submissions",
        ["submitted_at"],
    )


def downgrade() -> None:
    op.drop_table("broker_submissions")
