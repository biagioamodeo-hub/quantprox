from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


def test_market_data_endpoints() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    def override_session() -> Session:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})
    try:
        instrument = client.post(
            "/api/v1/market-data/instruments", json={"symbol": "AAPL"}
        )
        assert instrument.status_code == 201
        assert instrument.json()["symbol"] == "AAPL"

        candle = client.post(
            "/api/v1/market-data/candles",
            json={
                "instrument_id": instrument.json()["id"],
                "timeframe": "1d",
                "open_time": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
                "open": "100.0",
                "high": "105.0",
                "low": "99.0",
                "close": "103.0",
                "volume": "1000000",
            },
        )
        assert candle.status_code == 201

        response = client.get(
            "/api/v1/market-data/candles",
            params={"instrument_id": instrument.json()["id"], "timeframe": "1d"},
        )
        assert response.status_code == 200
        assert response.json()[0]["close"] == "103.00000000"
    finally:
        app.dependency_overrides.clear()
