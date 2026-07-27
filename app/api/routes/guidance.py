from fastapi import APIRouter

from app.schemas.guidance import GuidedPlanCreate, GuidedPlanRead
from app.services.guidance import create_guided_plan

router = APIRouter()


@router.post("/plan", response_model=GuidedPlanRead)
def build_guided_plan(payload: GuidedPlanCreate) -> GuidedPlanRead:
    return create_guided_plan(payload)
