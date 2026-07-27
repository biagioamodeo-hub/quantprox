from fastapi import APIRouter

from app.schemas.guidance import (
    ActionSignalCreate,
    ActionSignalRead,
    GuidedPlanCreate,
    GuidedPlanRead,
    PurchaseSafetyCreate,
    PurchaseSafetyRead,
)
from app.services.guidance import (
    assess_action_signal,
    assess_purchase_safety,
    create_guided_plan,
)

router = APIRouter()


@router.post("/plan", response_model=GuidedPlanRead)
def build_guided_plan(payload: GuidedPlanCreate) -> GuidedPlanRead:
    return create_guided_plan(payload)


@router.post("/purchase-safety", response_model=PurchaseSafetyRead)
def check_purchase_safety(payload: PurchaseSafetyCreate) -> PurchaseSafetyRead:
    return assess_purchase_safety(payload)


@router.post("/action-signal", response_model=ActionSignalRead)
def check_action_signal(payload: ActionSignalCreate) -> ActionSignalRead:
    return assess_action_signal(payload)
