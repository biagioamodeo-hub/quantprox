from decimal import Decimal
from typing import Literal, cast

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.decisions import Decision
from app.repositories.decisions import DecisionRepository
from app.schemas.decisions import DecisionEvaluate, DecisionOrderCreate, DecisionRead
from app.schemas.orders import OrderCreate, OrderRead
from app.services.access import TenantAccess
from app.services.orders import OrderService


class DecisionService:
    def __init__(self, session: Session, tenant_id: str) -> None:
        self.repository = DecisionRepository(session)
        self.order_service = OrderService(session, tenant_id)
        self.access = TenantAccess(session, tenant_id)

    def evaluate(self, payload: DecisionEvaluate) -> DecisionRead:
        self.access.require_portfolio(payload.portfolio_id)
        candles = self.repository.recent_candles(
            payload.instrument_id, payload.timeframe, payload.long_window
        )
        short_average: Decimal | None = None
        long_average: Decimal | None = None
        action = "hold"

        if len(candles) < payload.long_window:
            rationale = (
                f"Insufficient data: {len(candles)} of "
                f"{payload.long_window} candles available."
            )
        else:
            short_average = (
                sum(
                    (candle.close for candle in candles[: payload.short_window]),
                    start=Decimal("0"),
                )
                / payload.short_window
            )
            long_average = (
                sum(
                    (candle.close for candle in candles),
                    start=Decimal("0"),
                )
                / payload.long_window
            )
            if short_average > long_average:
                action = "buy"
                rationale = "Short moving average is above the long moving average."
            elif short_average < long_average:
                action = "sell"
                rationale = "Short moving average is below the long moving average."
            else:
                rationale = "Short and long moving averages are equal."

        decision = Decision(
            **payload.model_dump(),
            short_average=short_average,
            long_average=long_average,
            action=action,
            rationale=rationale,
        )
        return DecisionRead.model_validate(self.repository.add(decision))

    def list_for_portfolio(self, portfolio_id: int) -> list[DecisionRead]:
        self.access.require_portfolio(portfolio_id)
        return [
            DecisionRead.model_validate(decision)
            for decision in self.repository.list_for_portfolio(portfolio_id)
        ]

    def create_order(
        self,
        decision_id: int,
        payload: DecisionOrderCreate,
        idempotency_key: str | None = None,
    ) -> OrderRead:
        decision = self.repository.get(decision_id)
        if decision is None:
            raise NotFoundError("Decision not found.")
        self.access.require_portfolio(decision.portfolio_id)
        if decision.action not in {"buy", "sell"}:
            raise ConflictError("Hold decisions cannot create orders.")
        side = cast(Literal["buy", "sell"], decision.action)
        return self.order_service.submit(
            OrderCreate(
                portfolio_id=decision.portfolio_id,
                instrument_id=decision.instrument_id,
                side=side,
                quantity=payload.quantity,
                limit_price=payload.limit_price,
            ),
            idempotency_key,
        )
