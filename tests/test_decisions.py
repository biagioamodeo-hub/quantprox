from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


def test_moving_average_decisions_are_audited() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    def override_session() -> Session:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    client = TestClient(app)
    try:
        instrument = client.post(
            "/api/v1/market-data/instruments", json={"symbol": "AAPL"}
        ).json()
        empty_instrument = client.post(
            "/api/v1/market-data/instruments", json={"symbol": "MSFT"}
        ).json()
        portfolio = client.post("/api/v1/portfolios", json={"name": "Signals"}).json()
        start = datetime(2026, 1, 1, tzinfo=UTC)
        for offset, close in enumerate(("100", "110", "120")):
            response = client.post(
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
            assert response.status_code == 201

        decision = client.post(
            "/api/v1/decisions/evaluate",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "timeframe": "1d",
                "short_window": 2,
                "long_window": 3,
            },
        )
        assert decision.status_code == 201
        assert decision.json()["action"] == "buy"

        hold = client.post(
            "/api/v1/decisions/evaluate",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": empty_instrument["id"],
                "timeframe": "1d",
                "short_window": 2,
                "long_window": 3,
            },
        )
        assert hold.status_code == 201
        assert hold.json()["action"] == "hold"
        assert hold.json()["short_average"] is None

        decisions = client.get(
            "/api/v1/decisions", params={"portfolio_id": portfolio["id"]}
        )
        assert decisions.status_code == 200
        assert [item["action"] for item in decisions.json()] == ["buy", "hold"]

        invalid = client.post(
            "/api/v1/decisions/evaluate",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "timeframe": "1d",
                "short_window": 3,
                "long_window": 2,
            },
        )
        assert invalid.status_code == 422
    finally:
        app.dependency_overrides.clear()
