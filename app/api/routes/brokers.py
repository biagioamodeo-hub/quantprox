from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import get_current_tenant
from app.schemas.brokers import (
    BrokerSubmissionRead,
    RevolutDemoPurchaseCreate,
    RevolutDemoPurchaseRead,
)
from app.services.brokers import BrokerService, create_revolut_demo_purchase

router = APIRouter()


def get_broker_service(
    session: Session = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant),
) -> BrokerService:
    return BrokerService(session, tenant_id)


@router.post(
    "/sandbox/orders/{order_id}",
    response_model=BrokerSubmissionRead,
    status_code=status.HTTP_201_CREATED,
)
def submit_order(
    order_id: int,
    service: BrokerService = Depends(get_broker_service),
) -> BrokerSubmissionRead:
    return service.submit(order_id)


@router.get(
    "/sandbox/orders/{order_id}",
    response_model=BrokerSubmissionRead,
)
def get_order(
    order_id: int,
    service: BrokerService = Depends(get_broker_service),
) -> BrokerSubmissionRead:
    return service.get(order_id)


@router.post(
    "/sandbox/orders/{order_id}/cancel",
    response_model=BrokerSubmissionRead,
)
def cancel_order(
    order_id: int,
    service: BrokerService = Depends(get_broker_service),
) -> BrokerSubmissionRead:
    return service.cancel(order_id)


@router.post(
    "/revolut-demo/purchases",
    response_model=RevolutDemoPurchaseRead,
    status_code=status.HTTP_201_CREATED,
)
def purchase_with_revolut_demo(
    payload: RevolutDemoPurchaseCreate,
) -> RevolutDemoPurchaseRead:
    return create_revolut_demo_purchase(payload)
