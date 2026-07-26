from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import get_current_tenant
from app.schemas.executions import ExecutionCreate, ExecutionRead
from app.services.executions import ExecutionService

router = APIRouter()


def get_execution_service(
    session: Session = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant),
) -> ExecutionService:
    return ExecutionService(session, tenant_id)


@router.post(
    "/orders/{order_id}",
    response_model=ExecutionRead,
    status_code=status.HTTP_201_CREATED,
)
def execute_order(
    order_id: int,
    payload: ExecutionCreate | None = None,
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key", min_length=1, max_length=128
    ),
    service: ExecutionService = Depends(get_execution_service),
) -> ExecutionRead:
    return service.execute(order_id, payload, idempotency_key)


@router.get("", response_model=list[ExecutionRead])
def list_executions(
    portfolio_id: int,
    service: ExecutionService = Depends(get_execution_service),
) -> list[ExecutionRead]:
    return service.list_for_portfolio(portfolio_id)
