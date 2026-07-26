from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import get_current_tenant
from app.schemas.risk import (
    PreTradeCheck,
    PreTradeCheckResult,
    RiskLimitRead,
    RiskLimitWrite,
)
from app.services.risk import RiskService

router = APIRouter()


def get_risk_service(
    session: Session = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant),
) -> RiskService:
    return RiskService(session, tenant_id)


@router.put("/limits/{portfolio_id}", response_model=RiskLimitRead)
def set_risk_limit(
    portfolio_id: int,
    payload: RiskLimitWrite,
    service: RiskService = Depends(get_risk_service),
) -> RiskLimitRead:
    return service.set_limit(portfolio_id, payload)


@router.get("/limits/{portfolio_id}", response_model=RiskLimitRead)
def get_risk_limit(
    portfolio_id: int,
    service: RiskService = Depends(get_risk_service),
) -> RiskLimitRead:
    risk_limit = service.get_limit(portfolio_id)
    if risk_limit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk limits are not configured for this portfolio.",
        )
    return risk_limit


@router.post("/checks/orders", response_model=PreTradeCheckResult)
def check_order(
    payload: PreTradeCheck,
    service: RiskService = Depends(get_risk_service),
) -> PreTradeCheckResult:
    return service.check_order(payload)
