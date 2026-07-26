from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_data import Candle
from app.models.portfolio import Portfolio, Position


class PortfolioRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_portfolio(self, portfolio: Portfolio) -> Portfolio:
        self.session.add(portfolio)
        self.session.commit()
        self.session.refresh(portfolio)
        return portfolio

    def list_portfolios(self, tenant_id: str) -> list[Portfolio]:
        return list(
            self.session.scalars(
                select(Portfolio)
                .where(Portfolio.tenant_id == tenant_id)
                .order_by(Portfolio.name)
            )
        )

    def add_position(self, position: Position) -> Position:
        self.session.add(position)
        self.session.commit()
        self.session.refresh(position)
        return position

    def list_positions(self, portfolio_id: int) -> list[Position]:
        statement = (
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .order_by(Position.instrument_id)
        )
        return list(self.session.scalars(statement))

    def get_portfolio(self, portfolio_id: int, tenant_id: str) -> Portfolio | None:
        return self.session.scalar(
            select(Portfolio).where(
                Portfolio.id == portfolio_id,
                Portfolio.tenant_id == tenant_id,
            )
        )

    def latest_close(self, instrument_id: int, timeframe: str) -> Decimal | None:
        statement = (
            select(Candle.close)
            .where(
                Candle.instrument_id == instrument_id,
                Candle.timeframe == timeframe,
            )
            .order_by(Candle.open_time.desc(), Candle.id.desc())
            .limit(1)
        )
        return self.session.scalar(statement)
