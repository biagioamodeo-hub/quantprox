from datetime import datetime

from sqlalchemy.orm import Session

from app.models.market_data import Candle, Instrument
from app.repositories.market_data import MarketDataRepository
from app.schemas.market_data import (
    CandleCreate,
    CandleRead,
    InstrumentCreate,
    InstrumentRead,
)


class MarketDataService:
    def __init__(self, session: Session) -> None:
        self.repository = MarketDataRepository(session)

    def create_instrument(self, payload: InstrumentCreate) -> InstrumentRead:
        instrument = Instrument(**payload.model_dump())
        return InstrumentRead.model_validate(self.repository.add_instrument(instrument))

    def list_instruments(self) -> list[InstrumentRead]:
        return [
            InstrumentRead.model_validate(instrument)
            for instrument in self.repository.list_instruments()
        ]

    def create_candle(self, payload: CandleCreate) -> CandleRead:
        candle = Candle(**payload.model_dump())
        return CandleRead.model_validate(self.repository.add_candle(candle))

    def list_candles(
        self,
        instrument_id: int,
        timeframe: str,
        start: datetime | None,
        end: datetime | None,
    ) -> list[CandleRead]:
        return [
            CandleRead.model_validate(candle)
            for candle in self.repository.list_candles(
                instrument_id, timeframe, start, end
            )
        ]
