from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    cash_balance: Decimal = Field(default=Decimal("0"), ge=0)


class PortfolioRead(PortfolioCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PositionCreate(BaseModel):
    portfolio_id: int = Field(gt=0)
    instrument_id: int = Field(gt=0)
    quantity: Decimal
    average_price: Decimal = Field(ge=0)


class PositionRead(PositionCreate):
    id: int
    realized_pnl: Decimal = Decimal("0")

    model_config = ConfigDict(from_attributes=True)


class PositionValuation(BaseModel):
    instrument_id: int
    quantity: Decimal
    average_price: Decimal
    mark_price: Decimal
    price_source: Literal["market", "cost_basis"]
    market_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal


class PortfolioValuation(BaseModel):
    portfolio_id: int
    cash_balance: Decimal
    positions_value: Decimal
    equity: Decimal
    gross_exposure: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    positions: list[PositionValuation]
