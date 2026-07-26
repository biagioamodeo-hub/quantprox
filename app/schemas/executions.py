from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExecutionCreate(BaseModel):
    quantity: Decimal | None = Field(default=None, gt=0)


class ExecutionRead(BaseModel):
    id: int
    order_id: int
    quantity: Decimal
    price: Decimal
    notional: Decimal
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)
