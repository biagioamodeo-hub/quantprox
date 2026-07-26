from fastapi import APIRouter

from app.api.routes.market_data import router as market_data_router
from app.api.routes.portfolio import router as portfolio_router

api_router = APIRouter()
api_router.include_router(
    market_data_router, prefix="/market-data", tags=["market-data"]
)
api_router.include_router(portfolio_router, prefix="/portfolios", tags=["portfolios"])
