from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class GuidedPlanCreate(BaseModel):
    starting_capital: Decimal = Field(default=Decimal("10000"), ge=1000, le=1000000)
    goal: Literal["preservation", "balanced", "growth"] = "balanced"
    experience: Literal["beginner", "experienced"] = "beginner"
    horizon_years: int = Field(default=5, ge=1, le=30)
    maximum_acceptable_loss_percent: Decimal = Field(default=Decimal("10"), ge=3, le=40)


class GuidedRiskProfile(BaseModel):
    code: Literal["cautious", "balanced", "dynamic"]
    label: str
    explanation: str
    allocation_percent: Decimal
    max_order_percent: Decimal
    stop_loss_percent: Decimal


class GuidedStrategy(BaseModel):
    name: str
    short_window: int
    long_window: int
    fee_percent: Decimal
    slippage_percent: Decimal


class GuidedBacktest(BaseModel):
    starting_capital: Decimal
    ending_equity: Decimal
    net_return_percent: Decimal
    benchmark_return_percent: Decimal
    maximum_drawdown_percent: Decimal
    trades: int
    profitable_trades: int
    costs_paid: Decimal
    tolerance_respected: bool
    success_rate_percent: Decimal
    risk_score: int = Field(ge=0, le=100)
    confidence_score: int = Field(ge=0, le=100)
    observations: int
    market_scenarios: int


class GuidedPlanRead(BaseModel):
    profile: GuidedRiskProfile
    strategy: GuidedStrategy
    backtest: GuidedBacktest
    max_order_notional: Decimal
    max_total_exposure: Decimal
    suggested_quantity: Decimal
    verdict: Literal["compatible", "review"]
    summary: str
    next_steps: list[str]
    warnings: list[str]
    disclaimer: str = (
        "Simulazione educativa basata su dati dimostrativi; non costituisce "
        "consulenza finanziaria né garantisce risultati futuri."
    )
