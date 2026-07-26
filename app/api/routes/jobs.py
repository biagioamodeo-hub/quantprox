from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import get_current_tenant
from app.schemas.decisions import DecisionEvaluate
from app.schemas.jobs import JobRead
from app.services.jobs import JobService

router = APIRouter()


def get_job_service(
    session: Session = Depends(get_db_session),
    tenant_id: str = Depends(get_current_tenant),
) -> JobService:
    return JobService(session, tenant_id)


@router.post(
    "/decisions/evaluate",
    response_model=JobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_decision(
    payload: DecisionEvaluate,
    idempotency_key: str | None = Header(
        default=None, alias="Idempotency-Key", min_length=1, max_length=128
    ),
    service: JobService = Depends(get_job_service),
) -> JobRead:
    return service.enqueue_decision(payload, idempotency_key)


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    service: JobService = Depends(get_job_service),
) -> JobRead:
    return service.get(job_id)
