from datetime import UTC, datetime
from typing import Literal, cast

from sqlalchemy.orm import Session

from app.adapters.broker import BrokerAdapter, BrokerOrderRequest
from app.adapters.sandbox import SandboxBrokerAdapter
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models.brokers import BrokerSubmission
from app.repositories.brokers import BrokerRepository
from app.schemas.brokers import BrokerSubmissionRead
from app.services.access import TenantAccess


def get_broker_adapter() -> BrokerAdapter:
    if settings.broker_provider == "sandbox":
        return SandboxBrokerAdapter()
    raise RuntimeError(f"Unsupported broker provider: {settings.broker_provider}")


class BrokerService:
    def __init__(
        self,
        session: Session,
        tenant_id: str,
        adapter: BrokerAdapter | None = None,
    ) -> None:
        self.repository = BrokerRepository(session)
        self.access = TenantAccess(session, tenant_id)
        self.adapter = adapter or get_broker_adapter()

    def submit(self, order_id: int) -> BrokerSubmissionRead:
        order = self.repository.get_order(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        self.access.require_portfolio(order.portfolio_id)
        existing = self.repository.get_submission(order.id)
        if existing is not None:
            return BrokerSubmissionRead.model_validate(existing)
        if order.status != "accepted":
            raise ConflictError("Only accepted, unfilled orders can be submitted.")
        instrument = self.repository.get_instrument(order.instrument_id)
        if instrument is None:
            raise NotFoundError("Instrument not found.")
        side = cast(Literal["buy", "sell"], order.side)
        result = self.adapter.place_order(
            BrokerOrderRequest(
                client_order_id=f"{order.portfolio_id}:{order.id}",
                symbol=instrument.symbol,
                side=side,
                quantity=order.quantity,
                limit_price=order.limit_price,
            )
        )
        submission = BrokerSubmission(
            order_id=order.id,
            provider=self.adapter.name,
            external_order_id=result.external_order_id,
            status=result.status,
        )
        return BrokerSubmissionRead.model_validate(self.repository.add(submission))

    def get(self, order_id: int) -> BrokerSubmissionRead:
        order = self.repository.get_order(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        self.access.require_portfolio(order.portfolio_id)
        submission = self.repository.get_submission(order.id)
        if submission is None:
            raise NotFoundError("Broker submission not found.")
        return BrokerSubmissionRead.model_validate(submission)

    def cancel(self, order_id: int) -> BrokerSubmissionRead:
        order = self.repository.get_order(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        self.access.require_portfolio(order.portfolio_id)
        submission = self.repository.get_submission(order.id)
        if submission is None:
            raise NotFoundError("Broker submission not found.")
        if submission.status != "accepted":
            raise ConflictError("Only accepted broker submissions can be cancelled.")
        result = self.adapter.cancel_order(submission.external_order_id)
        submission.status = result.status
        submission.updated_at = datetime.now(UTC)
        order.status = "cancelled"
        order.cancelled_at = submission.updated_at
        return BrokerSubmissionRead.model_validate(self.repository.commit(submission))
