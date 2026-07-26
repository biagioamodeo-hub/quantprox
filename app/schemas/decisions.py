from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DecisionEvaluate(BaseModel):
    portfolio_id: int = Field(gt=0)
    instrument_id: int = Field(gt=0)
    timeframe: str = Field(min_length=1, max_length=8)
    short_window: int = Field(default=5, ge=1, le=200)
    long_window: int = Field(default=20, ge=2, le=500)

    @model_validator(mode="after")
    def validate_windows(self) -> "DecisionEvaluate":
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be less than long_window")
        return self


class DecisionRead(DecisionEvaluate):
    id: int
    short_average: Decimal | None
    long_average: Decimal | None
    action: Literal["buy", "sell", "hold"]
    rationale: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
