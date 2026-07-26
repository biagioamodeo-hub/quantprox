from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_data import Candle
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

    def positions(self, portfolio_id: int) -> list[Position]:
        return list(
            self.session.scalars(
                select(Position).where(Position.portfolio_id == portfolio_id)
            )
        )

    def latest_close(self, instrument_id: int) -> Decimal | None:
        statement = (
            select(Candle.close)
            .where(Candle.instrument_id == instrument_id)
            .order_by(Candle.open_time.desc(), Candle.id.desc())
            .limit(1)
        )
        return self.session.scalar(statement)
