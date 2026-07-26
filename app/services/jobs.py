from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.jobs import Job
from app.repositories.jobs import JobRepository
from app.schemas.decisions import DecisionEvaluate
from app.schemas.jobs import JobRead
from app.services.access import TenantAccess
from app.services.decisions import DecisionService
from app.utils.idempotency import request_fingerprint


class JobService:
    def __init__(self, session: Session, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.repository = JobRepository(session)
        self.access = TenantAccess(session, tenant_id)

    def enqueue_decision(
        self,
        payload: DecisionEvaluate,
        idempotency_key: str | None = None,
    ) -> JobRead:
        self.access.require_portfolio(payload.portfolio_id)
        fingerprint = request_fingerprint(payload)
        if idempotency_key is not None:
            existing = self.repository.get_by_idempotency_key(
                self.tenant_id, idempotency_key
            )
            if existing is not None:
                if existing.request_fingerprint != fingerprint:
                    raise ConflictError(
                        "Idempotency-Key was already used with a different payload."
                    )
                return JobRead.model_validate(existing)
        job = Job(
            tenant_id=self.tenant_id,
            kind="decision.evaluate",
            payload=payload.model_dump(mode="json"),
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint if idempotency_key else None,
        )
        return JobRead.model_validate(self.repository.add(job))

    def get(self, job_id: int) -> JobRead:
        job = self.repository.get(job_id, self.tenant_id)
        if job is None:
            raise NotFoundError("Job not found.")
        return JobRead.model_validate(job)


def process_next_job(session: Session) -> Job | None:
    repository = JobRepository(session)
    job = repository.claim_next()
    if job is None:
        return None
    job_id = job.id
    try:
        if job.kind != "decision.evaluate":
            raise ValueError(f"Unsupported job kind: {job.kind}")
        payload = DecisionEvaluate.model_validate(job.payload)
        result = DecisionService(session, job.tenant_id).evaluate(payload, job.id)
        return repository.complete(job.id, result.model_dump(mode="json"))
    except Exception as exception:
        session.rollback()
        return repository.fail(job_id, str(exception))
