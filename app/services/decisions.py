from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.decisions import Decision
from app.repositories.decisions import DecisionRepository
from app.schemas.decisions import DecisionEvaluate, DecisionRead


class DecisionService:
    def __init__(self, session: Session) -> None:
        self.repository = DecisionRepository(session)

    def evaluate(self, payload: DecisionEvaluate) -> DecisionRead:
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
        return [
            DecisionRead.model_validate(decision)
            for decision in self.repository.list_for_portfolio(portfolio_id)
        ]
