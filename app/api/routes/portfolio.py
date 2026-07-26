from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import get_current_tenant
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioRead,
    PortfolioValuation,
    PositionCreate,
    PositionRead,
)
from app.services.portfolio import PortfolioService

router = APIRouter()


def get_portfolio_service(
    session: Session = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant),
) -> PortfolioService:
    return PortfolioService(session, tenant_id)


@router.post("", response_model=PortfolioRead, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    payload: PortfolioCreate,
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioRead:
    return service.create_portfolio(payload)


@router.get("", response_model=list[PortfolioRead])
def list_portfolios(
    service: PortfolioService = Depends(get_portfolio_service),
) -> list[PortfolioRead]:
    return service.list_portfolios()


@router.post(
    "/positions", response_model=PositionRead, status_code=status.HTTP_201_CREATED
)
def create_position(
    payload: PositionCreate,
    service: PortfolioService = Depends(get_portfolio_service),
) -> PositionRead:
    return service.create_position(payload)


@router.get("/{portfolio_id}/positions", response_model=list[PositionRead])
def list_positions(
    portfolio_id: int,
    service: PortfolioService = Depends(get_portfolio_service),
) -> list[PositionRead]:
    return service.list_positions(portfolio_id)


@router.get("/{portfolio_id}/valuation", response_model=PortfolioValuation)
def value_portfolio(
    portfolio_id: int,
    timeframe: str = "1d",
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioValuation:
    return service.value_portfolio(portfolio_id, timeframe)
