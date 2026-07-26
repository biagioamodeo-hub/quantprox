from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.observability import metrics

router = APIRouter()


@router.get("", response_class=PlainTextResponse)
def prometheus_metrics() -> str:
    return metrics.render()
