from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), index=True)
    timeframe: Mapped[str] = mapped_column(String(8))
    short_window: Mapped[int]
    long_window: Mapped[int]
    short_average: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    long_average: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    action: Mapped[str] = mapped_column(String(4), index=True)
    rationale: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
