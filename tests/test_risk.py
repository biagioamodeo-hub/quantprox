from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


def test_pre_trade_risk_checks() -> None:
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
        ).json()
        portfolio = client.post(
            "/api/v1/portfolios", json={"name": "Risk managed"}
        ).json()
        client.post(
            "/api/v1/portfolios/positions",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "quantity": "10",
                "average_price": "100",
            },
        )

        missing = client.get(f"/api/v1/risk/limits/{portfolio['id']}")
        assert missing.status_code == 404

        configured = client.put(
            f"/api/v1/risk/limits/{portfolio['id']}",
            json={
                "max_order_notional": "500",
                "max_total_exposure": "1400",
            },
        )
        assert configured.status_code == 200
        updated = client.put(
            f"/api/v1/risk/limits/{portfolio['id']}",
            json={
                "max_order_notional": "500",
                "max_total_exposure": "1400",
            },
        )
        assert updated.json()["id"] == configured.json()["id"]
        assert client.get(f"/api/v1/risk/limits/{portfolio['id']}").status_code == 200

        accepted = client.post(
            "/api/v1/risk/checks/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "buy",
                "quantity": "2",
                "price": "100",
            },
        )
        assert accepted.status_code == 200
        assert accepted.json()["accepted"] is True
        assert Decimal(accepted.json()["current_exposure"]) == Decimal("1000")

        exposure_rejected = client.post(
            "/api/v1/risk/checks/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "buy",
                "quantity": "5",
                "price": "100",
            },
        )
        assert exposure_rejected.status_code == 200
        assert exposure_rejected.json()["accepted"] is False
        assert exposure_rejected.json()["reason"] == (
            "Projected exposure exceeds the configured limit."
        )

        order_rejected = client.post(
            "/api/v1/risk/checks/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "buy",
                "quantity": "6",
                "price": "100",
            },
        )
        assert order_rejected.json()["reason"] == (
            "Order notional exceeds the configured limit."
        )

        unconfigured_portfolio = client.post(
            "/api/v1/portfolios", json={"name": "Unconfigured"}
        ).json()
        unconfigured = client.post(
            "/api/v1/risk/checks/orders",
            json={
                "portfolio_id": unconfigured_portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "buy",
                "quantity": "1",
                "price": "100",
            },
        )
        assert unconfigured.json()["accepted"] is False
        assert unconfigured.json()["reason"] == (
            "Risk limits are not configured for this portfolio."
        )

        reducing_sell = client.post(
            "/api/v1/risk/checks/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "sell",
                "quantity": "2",
                "price": "100",
            },
        )
        assert reducing_sell.json()["accepted"] is True
        assert Decimal(reducing_sell.json()["projected_exposure"]) == Decimal("800")
    finally:
        app.dependency_overrides.clear()
