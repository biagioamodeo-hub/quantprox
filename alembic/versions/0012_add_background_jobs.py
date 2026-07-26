"""Add persistent background jobs.

Revision ID: 0012_background_jobs
Revises: 0011_idempotency_keys
Create Date: 2026-07-26
"""

import sqlalchemy as sa

from alembic import op

revision = "0012_background_jobs"
down_revision = "0011_idempotency_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "idempotency_key",
            name="uq_job_tenant_idempotency_key",
        ),
    )
    op.create_index("ix_jobs_tenant_id", "jobs", ["tenant_id"])
    op.create_index("ix_jobs_kind", "jobs", ["kind"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])
    op.add_column("decisions", sa.Column("job_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_decisions_job_id", "decisions", "jobs", ["job_id"], ["id"]
    )
    op.create_index("ix_decisions_job_id", "decisions", ["job_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_decisions_job_id", table_name="decisions")
    op.drop_constraint("fk_decisions_job_id", "decisions", type_="foreignkey")
    op.drop_column("decisions", "job_id")
    op.drop_table("jobs")
