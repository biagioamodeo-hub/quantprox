from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brokers import BrokerSubmission
from app.models.market_data import Instrument
from app.models.orders import Order


class BrokerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_order(self, order_id: int) -> Order | None:
        return self.session.get(Order, order_id, with_for_update=True)

    def get_instrument(self, instrument_id: int) -> Instrument | None:
        return self.session.get(Instrument, instrument_id)

    def get_submission(self, order_id: int) -> BrokerSubmission | None:
        return self.session.scalar(
            select(BrokerSubmission).where(BrokerSubmission.order_id == order_id)
        )

    def add(self, submission: BrokerSubmission) -> BrokerSubmission:
        self.session.add(submission)
        self.session.commit()
        self.session.refresh(submission)
        return submission

    def commit(self, submission: BrokerSubmission) -> BrokerSubmission:
        self.session.commit()
        self.session.refresh(submission)
        return submission
