from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RiskLimitWrite(BaseModel):
    max_order_notional: Decimal = Field(gt=0)
    max_total_exposure: Decimal = Field(gt=0)


class RiskLimitRead(RiskLimitWrite):
    id: int
    portfolio_id: int

    model_config = ConfigDict(from_attributes=True)


class PreTradeCheck(BaseModel):
    portfolio_id: int = Field(gt=0)
    instrument_id: int = Field(gt=0)
    side: Literal["buy", "sell"]
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)


class PreTradeCheckResult(BaseModel):
    accepted: bool
    order_notional: Decimal
    current_exposure: Decimal
    projected_exposure: Decimal
    reason: str | None = None
