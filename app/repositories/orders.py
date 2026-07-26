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

    def get(self, order_id: int) -> Order | None:
        return self.session.get(Order, order_id)

    def get_by_idempotency_key(
        self, portfolio_id: int, idempotency_key: str
    ) -> Order | None:
        return self.session.scalar(
            select(Order).where(
                Order.portfolio_id == portfolio_id,
                Order.idempotency_key == idempotency_key,
            )
        )

    def commit(self, order: Order) -> Order:
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
