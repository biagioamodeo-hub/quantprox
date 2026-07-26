from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.models.jobs import Job
from app.services.jobs import process_next_job


def test_persistent_tenant_isolated_decision_job() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    def override_session() -> Session:
        with session_factory() as session:
            yield session

    previous_keys = settings.tenant_api_keys
    settings.tenant_api_keys = {
        "demo": "dev-api-key",
        "other": "other-api-key",
    }
    app.dependency_overrides[get_db_session] = override_session
    demo = TestClient(app, headers={"X-API-Key": "dev-api-key"})
    other = TestClient(app, headers={"X-API-Key": "other-api-key"})
    try:
        instrument = demo.post(
            "/api/v1/market-data/instruments", json={"symbol": "ASYNC"}
        ).json()
        portfolio = demo.post("/api/v1/portfolios", json={"name": "Async"}).json()
        start = datetime(2026, 1, 1, tzinfo=UTC)
        for offset, close in enumerate(("100", "110", "120")):
            demo.post(
                "/api/v1/market-data/candles",
                json={
                    "instrument_id": instrument["id"],
                    "timeframe": "1d",
                    "open_time": (start + timedelta(days=offset)).isoformat(),
                    "open": close,
                    "high": close,
                    "low": close,
                    "close": close,
                    "volume": "1000",
                },
            )

        payload = {
            "portfolio_id": portfolio["id"],
            "instrument_id": instrument["id"],
            "timeframe": "1d",
            "short_window": 2,
            "long_window": 3,
        }
        headers = {"Idempotency-Key": "decision-job-1"}
        queued = demo.post(
            "/api/v1/jobs/decisions/evaluate",
            json=payload,
            headers=headers,
        )
        replayed = demo.post(
            "/api/v1/jobs/decisions/evaluate",
            json=payload,
            headers=headers,
        )
        assert queued.status_code == replayed.status_code == 202
        assert replayed.json()["id"] == queued.json()["id"]
        assert queued.json()["status"] == "queued"
        mismatch = demo.post(
            "/api/v1/jobs/decisions/evaluate",
            json={**payload, "long_window": 4},
            headers=headers,
        )
        assert mismatch.status_code == 409
        assert other.get(f"/api/v1/jobs/{queued.json()['id']}").status_code == 404

        with session_factory() as session:
            completed = process_next_job(session)
            assert completed is not None
            assert completed.status == "succeeded"
            assert completed.attempts == 1

        result = demo.get(f"/api/v1/jobs/{queued.json()['id']}")
        assert result.status_code == 200
        assert result.json()["status"] == "succeeded"
        assert result.json()["result"]["action"] == "buy"
        decisions = demo.get(
            "/api/v1/decisions", params={"portfolio_id": portfolio["id"]}
        )
        assert len(decisions.json()) == 1

        with session_factory() as session:
            assert process_next_job(session) is None

        with session_factory() as session:
            invalid = Job(
                tenant_id="demo",
                kind="unsupported",
                payload={},
                max_attempts=1,
            )
            session.add(invalid)
            session.commit()
            invalid_id = invalid.id
            failed = process_next_job(session)
            assert failed is not None
            assert failed.status == "failed"
            assert failed.attempts == 1
        failed_response = demo.get(f"/api/v1/jobs/{invalid_id}")
        assert failed_response.json()["status"] == "failed"
        assert "Unsupported job kind" in failed_response.json()["error"]
    finally:
        settings.tenant_api_keys = previous_keys
        app.dependency_overrides.clear()
