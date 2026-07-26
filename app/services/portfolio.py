from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.portfolio import Portfolio, Position
from app.repositories.portfolio import PortfolioRepository
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioRead,
    PortfolioValuation,
    PositionCreate,
    PositionRead,
    PositionValuation,
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

    def value_portfolio(self, portfolio_id: int, timeframe: str) -> PortfolioValuation:
        portfolio = self.repository.get_portfolio(portfolio_id)
        if portfolio is None:
            raise NotFoundError("Portfolio not found.")

        valuations: list[PositionValuation] = []
        for position in self.repository.list_positions(portfolio_id):
            market_price = self.repository.latest_close(
                position.instrument_id, timeframe
            )
            mark_price = market_price or position.average_price
            market_value = position.quantity * mark_price
            valuations.append(
                PositionValuation(
                    instrument_id=position.instrument_id,
                    quantity=position.quantity,
                    average_price=position.average_price,
                    mark_price=mark_price,
                    price_source="market" if market_price is not None else "cost_basis",
                    market_value=market_value,
                    unrealized_pnl=position.quantity
                    * (mark_price - position.average_price),
                    realized_pnl=position.realized_pnl,
                )
            )

        positions_value = sum(
            (item.market_value for item in valuations), start=Decimal("0")
        )
        unrealized_pnl = sum(
            (item.unrealized_pnl for item in valuations), start=Decimal("0")
        )
        realized_pnl = sum(
            (item.realized_pnl for item in valuations), start=Decimal("0")
        )
        return PortfolioValuation(
            portfolio_id=portfolio.id,
            cash_balance=portfolio.cash_balance,
            positions_value=positions_value,
            equity=portfolio.cash_balance + positions_value,
            gross_exposure=sum(
                (abs(item.market_value) for item in valuations), start=Decimal("0")
            ),
            unrealized_pnl=unrealized_pnl,
            realized_pnl=realized_pnl,
            positions=valuations,
        )
