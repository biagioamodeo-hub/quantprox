from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BrokerSubmission(Base):
    __tablename__ = "broker_submissions"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_order_id",
            name="uq_broker_submission_external_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), unique=True, index=True
    )
    provider: Mapped[str] = mapped_column(String(32), index=True)
    external_order_id: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), index=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
