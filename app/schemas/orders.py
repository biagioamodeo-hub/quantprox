from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    portfolio_id: int = Field(gt=0)
    instrument_id: int = Field(gt=0)
    side: Literal["buy", "sell"]
    quantity: Decimal = Field(gt=0)
    limit_price: Decimal = Field(gt=0)


class OrderRead(OrderCreate):
    id: int
    status: Literal["accepted", "rejected", "partially_filled", "filled", "cancelled"]
    filled_quantity: Decimal
    remaining_quantity: Decimal
    rejection_reason: str | None
    cancelled_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
