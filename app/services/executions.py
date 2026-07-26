from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, UnprocessableError
from app.models.executions import Execution
from app.models.portfolio import Position
from app.repositories.executions import ExecutionRepository
from app.schemas.executions import ExecutionRead


class ExecutionService:
    def __init__(self, session: Session) -> None:
        self.repository = ExecutionRepository(session)

    def execute(self, order_id: int) -> ExecutionRead:
        order = self.repository.get_order(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        if order.status != "accepted":
            raise ConflictError("Only accepted orders can be executed.")
        if self.repository.get_for_order(order_id) is not None:
            raise ConflictError("Order has already been executed.")

        portfolio = self.repository.get_portfolio(order.portfolio_id)
        if portfolio is None:
            raise NotFoundError("Portfolio not found.")

        notional = order.quantity * order.limit_price
        position = self.repository.get_position(order.portfolio_id, order.instrument_id)
        if order.side == "buy":
            if portfolio.cash_balance < notional:
                raise UnprocessableError("Insufficient portfolio cash.")
            portfolio.cash_balance -= notional
            if position is None:
                position = Position(
                    portfolio_id=order.portfolio_id,
                    instrument_id=order.instrument_id,
                    quantity=order.quantity,
                    average_price=order.limit_price,
                )
                self.repository.add_position(position)
            else:
                total_cost = position.quantity * position.average_price + notional
                position.quantity += order.quantity
                position.average_price = total_cost / position.quantity
        else:
            if position is None or position.quantity < order.quantity:
                raise UnprocessableError("Insufficient position quantity.")
            position.realized_pnl += order.quantity * (
                order.limit_price - position.average_price
            )
            position.quantity -= order.quantity
            portfolio.cash_balance += notional

        order.status = "filled"
        execution = Execution(
            order_id=order.id,
            quantity=order.quantity,
            price=order.limit_price,
            notional=notional,
        )
        return ExecutionRead.model_validate(self.repository.commit(execution))

    def list_for_portfolio(self, portfolio_id: int) -> list[ExecutionRead]:
        return [
            ExecutionRead.model_validate(execution)
            for execution in self.repository.list_for_portfolio(portfolio_id)
        ]
