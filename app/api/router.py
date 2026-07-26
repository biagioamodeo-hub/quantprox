from fastapi import APIRouter, Depends

from app.api.routes.decisions import router as decisions_router
from app.api.routes.executions import router as executions_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.market_data import router as market_data_router
from app.api.routes.orders import router as orders_router
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.risk import router as risk_router
from app.dependencies.auth import get_current_tenant

api_router = APIRouter(dependencies=[Depends(get_current_tenant)])
api_router.include_router(decisions_router, prefix="/decisions", tags=["decisions"])
api_router.include_router(executions_router, prefix="/executions", tags=["executions"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(
    market_data_router, prefix="/market-data", tags=["market-data"]
)
api_router.include_router(orders_router, prefix="/orders", tags=["orders"])
api_router.include_router(portfolio_router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(risk_router, prefix="/risk", tags=["risk"])
