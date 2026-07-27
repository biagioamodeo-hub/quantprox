from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.market_data import (
    CandleCreate,
    CandleRead,
    ExchangeRateRead,
    InstrumentCreate,
    InstrumentRead,
)
from app.services.exchange_rates import get_exchange_rate
from app.services.market_data import MarketDataService

router = APIRouter()


@router.get("/exchange-rate", response_model=ExchangeRateRead)
def read_exchange_rate(
    base: str = Query(min_length=3, max_length=3),
    quote: str = Query(min_length=3, max_length=3),
) -> ExchangeRateRead:
    try:
        return get_exchange_rate(base, quote)
    except Exception as exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Exchange-rate data is temporarily unavailable.",
        ) from exception


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
