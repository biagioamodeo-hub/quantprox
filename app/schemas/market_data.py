from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InstrumentCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    exchange: str | None = Field(default=None, max_length=64)
    currency: str = Field(default="USD", min_length=3, max_length=3)


class InstrumentRead(InstrumentCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CandleCreate(BaseModel):
    instrument_id: int
    timeframe: str = Field(min_length=1, max_length=8)
    open_time: datetime
    open: Decimal = Field(ge=0)
    high: Decimal = Field(ge=0)
    low: Decimal = Field(ge=0)
    close: Decimal = Field(ge=0)
    volume: Decimal = Field(ge=0)


class CandleRead(CandleCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
