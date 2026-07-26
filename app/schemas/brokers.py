from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class BrokerSubmissionRead(BaseModel):
    id: int
    order_id: int
    provider: str
    external_order_id: str
    status: Literal["accepted", "cancelled"]
    submitted_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
