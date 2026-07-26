from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.orders import Order
from app.repositories.orders import OrderRepository
from app.schemas.orders import OrderCreate, OrderRead
from app.schemas.risk import PreTradeCheck
from app.services.access import TenantAccess
from app.services.risk import RiskService
from app.utils.idempotency import request_fingerprint


class OrderService:
    def __init__(self, session: Session, tenant_id: str) -> None:
        self.repository = OrderRepository(session)
        self.risk_service = RiskService(session, tenant_id)
        self.access = TenantAccess(session, tenant_id)

    def submit(
        self, payload: OrderCreate, idempotency_key: str | None = None
    ) -> OrderRead:
        self.access.require_portfolio(payload.portfolio_id)
        fingerprint = request_fingerprint(payload)
        if idempotency_key is not None:
            existing = self.repository.get_by_idempotency_key(
                payload.portfolio_id, idempotency_key
            )
            if existing is not None:
                if existing.request_fingerprint != fingerprint:
                    raise ConflictError(
                        "Idempotency-Key was already used with a different payload."
                    )
                return OrderRead.model_validate(existing)
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
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint if idempotency_key else None,
        )
        return OrderRead.model_validate(self.repository.add(order))

    def list_for_portfolio(self, portfolio_id: int) -> list[OrderRead]:
        self.access.require_portfolio(portfolio_id)
        return [
            OrderRead.model_validate(order)
            for order in self.repository.list_for_portfolio(portfolio_id)
        ]

    def cancel(self, order_id: int) -> OrderRead:
        order = self.repository.get(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        self.access.require_portfolio(order.portfolio_id)
        if order.status not in {"accepted", "partially_filled"}:
            raise ConflictError("Only open orders can be cancelled.")
        order.status = "cancelled"
        order.cancelled_at = datetime.now(UTC)
        return OrderRead.model_validate(self.repository.commit(order))
