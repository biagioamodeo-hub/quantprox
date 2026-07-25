from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.market_data import (
    CandleCreate,
    CandleRead,
    InstrumentCreate,
    InstrumentRead,
)
from app.services.market_data import MarketDataService

router = APIRouter()


def get_market_data_service(
    session: Session = Depends(get_db_session),
) -> MarketDataService:
    return MarketDataService(session)


@router.post(
    "/instruments", response_model=InstrumentRead, status_code=status.HTTP_201_CREATED
)
def create_instrument(
    payload: InstrumentCreate,
    service: MarketDataService = Depends(get_market_data_service),
) -> InstrumentRead:
    return service.create_instrument(payload)


@router.get("/instruments", response_model=list[InstrumentRead])
def list_instruments(
    service: MarketDataService = Depends(get_market_data_service),
) -> list[InstrumentRead]:
    return service.list_instruments()


@router.post("/candles", response_model=CandleRead, status_code=status.HTTP_201_CREATED)
def create_candle(
    payload: CandleCreate,
    service: MarketDataService = Depends(get_market_data_service),
) -> CandleRead:
    return service.create_candle(payload)


@router.get("/candles", response_model=list[CandleRead])
def list_candles(
    instrument_id: int,
    timeframe: str,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    service: MarketDataService = Depends(get_market_data_service),
) -> list[CandleRead]:
    return service.list_candles(instrument_id, timeframe, start, end)
