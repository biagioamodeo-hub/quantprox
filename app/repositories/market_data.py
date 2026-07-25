from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.market_data import Candle, Instrument


class MarketDataRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_instrument(self, instrument: Instrument) -> Instrument:
        self.session.add(instrument)
        self.session.commit()
        self.session.refresh(instrument)
        return instrument

    def list_instruments(self) -> list[Instrument]:
        return list(
            self.session.scalars(select(Instrument).order_by(Instrument.symbol))
        )

    def add_candle(self, candle: Candle) -> Candle:
        self.session.add(candle)
        self.session.commit()
        self.session.refresh(candle)
        return candle

    def list_candles(
        self,
        instrument_id: int,
        timeframe: str,
        start: datetime | None,
        end: datetime | None,
    ) -> list[Candle]:
        statement: Select[tuple[Candle]] = select(Candle).where(
            Candle.instrument_id == instrument_id,
            Candle.timeframe == timeframe,
        )
        if start is not None:
            statement = statement.where(Candle.open_time >= start)
        if end is not None:
            statement = statement.where(Candle.open_time <= end)
        return list(self.session.scalars(statement.order_by(Candle.open_time)))
