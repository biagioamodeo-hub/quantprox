from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.schemas.orders import OrderCreate, OrderRead
from app.services.orders import OrderService

router = APIRouter()


def get_order_service(
    session: Session = Depends(get_db_session),
) -> OrderService:
    return OrderService(session)


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def submit_order(
    payload: OrderCreate,
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    return service.submit(payload)


@router.get("", response_model=list[OrderRead])
def list_orders(
    portfolio_id: int,
    service: OrderService = Depends(get_order_service),
) -> list[OrderRead]:
    return service.list_for_portfolio(portfolio_id)


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
) -> OrderRead:
    return service.cancel(order_id)
