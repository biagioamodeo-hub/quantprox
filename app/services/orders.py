from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.orders import Order
from app.repositories.orders import OrderRepository
from app.schemas.orders import OrderCreate, OrderRead
from app.schemas.risk import PreTradeCheck
from app.services.risk import RiskService


class OrderService:
    def __init__(self, session: Session) -> None:
        self.repository = OrderRepository(session)
        self.risk_service = RiskService(session)

    def submit(self, payload: OrderCreate) -> OrderRead:
        risk_result = self.risk_service.check_order(
            PreTradeCheck(
                portfolio_id=payload.portfolio_id,
                instrument_id=payload.instrument_id,
                side=payload.side,
                quantity=payload.quantity,
                price=payload.limit_price,
            )
        )
        order = Order(
            **payload.model_dump(),
            status="accepted" if risk_result.accepted else "rejected",
            rejection_reason=risk_result.reason,
        )
        return OrderRead.model_validate(self.repository.add(order))

    def list_for_portfolio(self, portfolio_id: int) -> list[OrderRead]:
        return [
            OrderRead.model_validate(order)
            for order in self.repository.list_for_portfolio(portfolio_id)
        ]

    def cancel(self, order_id: int) -> OrderRead:
        order = self.repository.get(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        if order.status != "accepted":
            raise ConflictError("Only accepted orders can be cancelled.")
        order.status = "cancelled"
        order.cancelled_at = datetime.now(UTC)
        return OrderRead.model_validate(self.repository.commit(order))
