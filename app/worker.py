import logging
import time

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.jobs import process_next_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quantprox.worker")


def run() -> None:
    logger.info("QuantProX worker started")
    while True:
        with SessionLocal() as session:
            try:
                job = process_next_job(session)
            except SQLAlchemyError:
                session.rollback()
                logger.exception("Job polling failed")
                job = None
        if job is None:
            time.sleep(settings.job_poll_interval_seconds)


if __name__ == "__main__":
    run()
