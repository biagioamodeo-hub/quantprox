from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import get_current_tenant
from app.schemas.decisions import (
    DecisionEvaluate,
    DecisionOrderCreate,
    DecisionRead,
)
from app.schemas.orders import OrderRead
from app.services.decisions import DecisionService

router = APIRouter()


def get_decision_service(
    session: Session = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant),
) -> DecisionService:
    return DecisionService(session, tenant_id)


@router.post(
    "/evaluate", response_model=DecisionRead, status_code=status.HTTP_201_CREATED
)
def evaluate_decision(
    payload: DecisionEvaluate,
    service: DecisionService = Depends(get_decision_service),
) -> DecisionRead:
    return service.evaluate(payload)


@router.get("", response_model=list[DecisionRead])
def list_decisions(
    portfolio_id: int,
    service: DecisionService = Depends(get_decision_service),
) -> list[DecisionRead]:
    return service.list_for_portfolio(portfolio_id)


@router.post(
    "/{decision_id}/orders",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
)
def create_order_from_decision(
    decision_id: int,
    payload: DecisionOrderCreate,
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key", min_length=1, max_length=128
    ),
    service: DecisionService = Depends(get_decision_service),
) -> OrderRead:
    return service.create_order(decision_id, payload, idempotency_key)
