from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ExecutionRead(BaseModel):
    id: int
    order_id: int
    quantity: Decimal
    price: Decimal
    notional: Decimal
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)
