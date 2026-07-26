from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.decisions import Decision
from app.models.market_data import Candle


class DecisionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def recent_candles(
        self, instrument_id: int, timeframe: str, limit: int
    ) -> list[Candle]:
        statement = (
            select(Candle)
            .where(
                Candle.instrument_id == instrument_id,
                Candle.timeframe == timeframe,
            )
            .order_by(Candle.open_time.desc())
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def add(self, decision: Decision) -> Decision:
        self.session.add(decision)
        self.session.commit()
        self.session.refresh(decision)
        return decision

    def list_for_portfolio(self, portfolio_id: int) -> list[Decision]:
        statement = (
            select(Decision)
            .where(Decision.portfolio_id == portfolio_id)
            .order_by(Decision.created_at, Decision.id)
        )
        return list(self.session.scalars(statement))
