from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio, Position
from app.repositories.portfolio import PortfolioRepository
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioRead,
    PositionCreate,
    PositionRead,
)


class PortfolioService:
    def __init__(self, session: Session) -> None:
        self.repository = PortfolioRepository(session)

    def create_portfolio(self, payload: PortfolioCreate) -> PortfolioRead:
        portfolio = Portfolio(**payload.model_dump())
        return PortfolioRead.model_validate(self.repository.add_portfolio(portfolio))

    def list_portfolios(self) -> list[PortfolioRead]:
        return [
            PortfolioRead.model_validate(portfolio)
            for portfolio in self.repository.list_portfolios()
        ]

    def create_position(self, payload: PositionCreate) -> PositionRead:
        position = Position(**payload.model_dump())
        return PositionRead.model_validate(self.repository.add_position(position))

    def list_positions(self, portfolio_id: int) -> list[PositionRead]:
        return [
            PositionRead.model_validate(position)
            for position in self.repository.list_positions(portfolio_id)
        ]
