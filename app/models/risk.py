from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RiskLimit(Base):
    __tablename__ = "risk_limits"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id"), unique=True, index=True
    )
    max_order_notional: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    max_total_exposure: Mapped[Decimal] = mapped_column(Numeric(24, 8))
