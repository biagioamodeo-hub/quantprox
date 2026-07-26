from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Position


class PortfolioRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_portfolio(self, portfolio: Portfolio) -> Portfolio:
        self.session.add(portfolio)
        self.session.commit()
        self.session.refresh(portfolio)
        return portfolio

    def list_portfolios(self) -> list[Portfolio]:
        return list(self.session.scalars(select(Portfolio).order_by(Portfolio.name)))

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
