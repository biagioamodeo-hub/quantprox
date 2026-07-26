from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.jobs import Job


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, job: Job) -> Job:
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get(self, job_id: int, tenant_id: str) -> Job | None:
        return self.session.scalar(
            select(Job).where(Job.id == job_id, Job.tenant_id == tenant_id)
        )

    def get_by_idempotency_key(
        self, tenant_id: str, idempotency_key: str
    ) -> Job | None:
        return self.session.scalar(
            select(Job).where(
                Job.tenant_id == tenant_id,
                Job.idempotency_key == idempotency_key,
            )
        )

    def claim_next(self) -> Job | None:
        job = self.session.scalar(
            select(Job)
            .where(Job.status == "queued", Job.attempts < Job.max_attempts)
            .order_by(Job.created_at, Job.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return None
        job.status = "running"
        job.attempts += 1
        job.started_at = datetime.now(UTC)
        job.error = None
        self.session.commit()
        self.session.refresh(job)
        return job

    def complete(self, job_id: int, result: dict[str, object]) -> Job:
        job = self.session.get_one(Job, job_id)
        job.status = "succeeded"
        job.result = result
        job.completed_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(job)
        return job

    def fail(self, job_id: int, detail: str) -> Job:
        job = self.session.get_one(Job, job_id)
        job.error = detail[:2000]
        job.status = "queued" if job.attempts < job.max_attempts else "failed"
        if job.status == "failed":
            job.completed_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(job)
        return job
