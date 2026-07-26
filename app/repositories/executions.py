from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.executions import Execution
from app.models.orders import Order
from app.models.portfolio import Portfolio, Position


class ExecutionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_order(self, order_id: int) -> Order | None:
        return self.session.get(Order, order_id)

    def get_portfolio(self, portfolio_id: int) -> Portfolio | None:
        return self.session.get(Portfolio, portfolio_id)

    def get_position(self, portfolio_id: int, instrument_id: int) -> Position | None:
        return self.session.scalar(
            select(Position).where(
                Position.portfolio_id == portfolio_id,
                Position.instrument_id == instrument_id,
            )
        )

    def add_position(self, position: Position) -> None:
        self.session.add(position)

    def commit(self, execution: Execution) -> Execution:
        self.session.add(execution)
        self.session.commit()
        self.session.refresh(execution)
        return execution

    def list_for_portfolio(self, portfolio_id: int) -> list[Execution]:
        statement = (
            select(Execution)
            .join(Order, Execution.order_id == Order.id)
            .where(Order.portfolio_id == portfolio_id)
            .order_by(Execution.executed_at, Execution.id)
        )
        return list(self.session.scalars(statement))
