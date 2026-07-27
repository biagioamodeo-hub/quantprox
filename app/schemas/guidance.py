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


class PurchaseSafetyCreate(BaseModel):
    asset_type: Literal[
        "auto", "stock", "bond", "government_bond", "crypto", "etf", "fund"
    ]
    available_capital: Decimal = Field(ge=100, le=1000000)
    requested_amount: Decimal = Field(ge=1, le=1000000)
    horizon_years: int = Field(ge=1, le=30)
    maximum_acceptable_loss_percent: Decimal = Field(ge=1, le=40)
    emergency_fund_available: bool
    market_regime: Literal["bullish", "neutral", "bearish"] = "neutral"
    goal: Literal["preservation", "income", "growth"] = "growth"


class PurchaseCandidate(BaseModel):
    asset_type: Literal["stock", "bond", "government_bond", "crypto", "etf", "fund"]
    label: str
    suitable: bool
    estimated_return_percent: Decimal
    risk_level: Literal["contenuto", "medio", "elevato", "molto elevato"]
    score: int = Field(ge=0, le=100)
    rationale: str


class PurchaseSafetyRead(BaseModel):
    asset_type: Literal["stock", "bond", "government_bond", "crypto", "etf", "fund"]
    asset_label: str
    outcome: Literal["proceed_simulation", "reduce_amount", "not_suitable"]
    outcome_label: str
    risk_level: Literal["contenuto", "medio", "elevato", "molto elevato"]
    max_allocation_percent: Decimal
    prudent_amount: Decimal
    requested_amount: Decimal
    checks_passed: int
    checks_total: int
    reasons: list[str]
    checklist: list[str]
    warning: str
    recommended_asset_type: str | None
    recommended_asset_label: str | None
    recommendation_summary: str
    ranking: list[PurchaseCandidate]
    disclaimer: str = (
        "Valutazione educativa e prudenziale: non garantisce la sicurezza "
        "dell'investimento e non sostituisce una consulenza finanziaria autorizzata."
    )


class ActionSignalCreate(BaseModel):
    owns_instrument: bool = False
    current_price: Decimal = Field(gt=0, le=10000000)
    average_purchase_price: Decimal | None = Field(default=None, gt=0, le=10000000)
    short_average: Decimal = Field(gt=0, le=10000000)
    long_average: Decimal = Field(gt=0, le=10000000)
    maximum_loss_percent: Decimal = Field(default=Decimal("10"), ge=1, le=40)


class ActionSignalRead(BaseModel):
    action: Literal["buy", "hold", "sell"]
    action_label: str
    confidence_score: int = Field(ge=0, le=100)
    trend: Literal["positive", "neutral", "negative"]
    trend_gap_percent: Decimal
    position_return_percent: Decimal | None
    rationale: str
    next_condition: str
    warnings: list[str]
    disclaimer: str = (
        "Segnale quantitativo educativo basato esclusivamente sui dati inseriti; "
        "non costituisce consulenza finanziaria e non garantisce risultati."
    )
