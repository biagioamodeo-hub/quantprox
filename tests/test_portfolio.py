from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


def test_portfolio_endpoints() -> None:
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
        portfolio = client.post(
            "/api/v1/portfolios",
            json={
                "name": "Core",
                "base_currency": "USD",
                "cash_balance": "10000",
            },
        )
        assert portfolio.status_code == 201
        assert portfolio.json()["cash_balance"] == "10000.00000000"

        position = client.post(
            "/api/v1/portfolios/positions",
            json={
                "portfolio_id": portfolio.json()["id"],
                "instrument_id": instrument.json()["id"],
                "quantity": "10",
                "average_price": "150.25",
            },
        )
        assert position.status_code == 201

        portfolios = client.get("/api/v1/portfolios")
        assert portfolios.status_code == 200
        assert portfolios.json()[0]["name"] == "Core"

        positions = client.get(f"/api/v1/portfolios/{portfolio.json()['id']}/positions")
        assert positions.status_code == 200
        assert positions.json()[0]["quantity"] == "10.00000000"

        client.post(
            "/api/v1/market-data/candles",
            json={
                "instrument_id": instrument.json()["id"],
                "timeframe": "1d",
                "open_time": datetime(2026, 1, 1, tzinfo=UTC).isoformat(),
                "open": "160",
                "high": "160",
                "low": "160",
                "close": "160",
                "volume": "1000",
            },
        )
        valuation = client.get(f"/api/v1/portfolios/{portfolio.json()['id']}/valuation")
        assert valuation.status_code == 200
        assert Decimal(valuation.json()["positions_value"]) == Decimal("1600")
        assert Decimal(valuation.json()["unrealized_pnl"]) == Decimal("97.5")
        assert valuation.json()["positions"][0]["price_source"] == "market"
    finally:
        app.dependency_overrides.clear()
