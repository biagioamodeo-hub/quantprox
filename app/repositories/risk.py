from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.portfolio import Position
from app.models.risk import RiskLimit
from app.schemas.risk import RiskLimitWrite


class RiskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_limit(self, portfolio_id: int) -> RiskLimit | None:
        return self.session.scalar(
            select(RiskLimit).where(RiskLimit.portfolio_id == portfolio_id)
        )

    def set_limit(self, portfolio_id: int, payload: RiskLimitWrite) -> RiskLimit:
        risk_limit = self.get_limit(portfolio_id)
        if risk_limit is None:
            risk_limit = RiskLimit(portfolio_id=portfolio_id, **payload.model_dump())
            self.session.add(risk_limit)
        else:
            risk_limit.max_order_notional = payload.max_order_notional
            risk_limit.max_total_exposure = payload.max_total_exposure
        self.session.commit()
        self.session.refresh(risk_limit)
        return risk_limit

    def current_exposure(self, portfolio_id: int) -> Decimal:
        statement = select(
            func.coalesce(
                func.sum(func.abs(Position.quantity * Position.average_price)), 0
            )
        ).where(Position.portfolio_id == portfolio_id)
        return Decimal(self.session.scalar(statement) or 0)
