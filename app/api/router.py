from fastapi import APIRouter

from app.api.routes.market_data import router as market_data_router

api_router = APIRouter()
api_router.include_router(
    market_data_router, prefix="/market-data", tags=["market-data"]
)
