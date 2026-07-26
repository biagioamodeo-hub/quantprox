from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), unique=True, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    notional: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
