from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), index=True)
    side: Mapped[str] = mapped_column(String(4))
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    filled_quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    limit_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    status: Mapped[str] = mapped_column(String(16), index=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(256))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )

    @property
    def remaining_quantity(self) -> Decimal:
        return self.quantity - self.filled_quantity
