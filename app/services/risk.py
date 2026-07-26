from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.risk import RiskRepository
from app.schemas.risk import (
    PreTradeCheck,
    PreTradeCheckResult,
    RiskLimitRead,
    RiskLimitWrite,
)


class RiskService:
    def __init__(self, session: Session) -> None:
        self.repository = RiskRepository(session)

    def get_limit(self, portfolio_id: int) -> RiskLimitRead | None:
        risk_limit = self.repository.get_limit(portfolio_id)
        if risk_limit is None:
            return None
        return RiskLimitRead.model_validate(risk_limit)

    def set_limit(self, portfolio_id: int, payload: RiskLimitWrite) -> RiskLimitRead:
        return RiskLimitRead.model_validate(
            self.repository.set_limit(portfolio_id, payload)
        )

    def check_order(self, payload: PreTradeCheck) -> PreTradeCheckResult:
        risk_limit = self.repository.get_limit(payload.portfolio_id)
        order_notional = abs(payload.quantity * payload.price)
        current_exposure = self.repository.current_exposure(payload.portfolio_id)
        projected_exposure = current_exposure + order_notional

        reason: str | None = None
        if risk_limit is None:
            reason = "Risk limits are not configured for this portfolio."
        elif order_notional > risk_limit.max_order_notional:
            reason = "Order notional exceeds the configured limit."
        elif projected_exposure > risk_limit.max_total_exposure:
            reason = "Projected exposure exceeds the configured limit."

        return PreTradeCheckResult(
            accepted=reason is None,
            order_notional=Decimal(order_notional),
            current_exposure=current_exposure,
            projected_exposure=projected_exposure,
            reason=reason,
        )
