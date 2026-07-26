from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orders import Order


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, order: Order) -> Order:
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return order

    def list_for_portfolio(self, portfolio_id: int) -> list[Order]:
        statement = (
            select(Order)
            .where(Order.portfolio_id == portfolio_id)
            .order_by(Order.created_at, Order.id)
        )
        return list(self.session.scalars(statement))
