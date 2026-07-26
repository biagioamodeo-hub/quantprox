from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


def test_order_submission_uses_risk_controls() -> None:
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
        portfolio = client.post("/api/v1/portfolios", json={"name": "Execution"}).json()
        client.put(
            f"/api/v1/risk/limits/{portfolio['id']}",
            json={
                "max_order_notional": "1000",
                "max_total_exposure": "5000",
            },
        )

        accepted = client.post(
            "/api/v1/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "buy",
                "quantity": "2",
                "limit_price": "150",
            },
        )
        assert accepted.status_code == 201
        assert accepted.json()["status"] == "accepted"
        assert accepted.json()["rejection_reason"] is None
        assert accepted.json()["cancelled_at"] is None

        rejected = client.post(
            "/api/v1/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "sell",
                "quantity": "10",
                "limit_price": "150",
            },
        )
        assert rejected.status_code == 201
        assert rejected.json()["status"] == "rejected"
        assert rejected.json()["rejection_reason"] == (
            "Order notional exceeds the configured limit."
        )

        orders = client.get("/api/v1/orders", params={"portfolio_id": portfolio["id"]})
        assert orders.status_code == 200
        assert [order["status"] for order in orders.json()] == [
            "accepted",
            "rejected",
        ]

        cancelled = client.post(f"/api/v1/orders/{accepted.json()['id']}/cancel")
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"
        assert cancelled.json()["cancelled_at"] is not None

        repeated = client.post(f"/api/v1/orders/{accepted.json()['id']}/cancel")
        assert repeated.status_code == 409
        assert repeated.json()["detail"] == ("Only open orders can be cancelled.")

        rejected_cancel = client.post(f"/api/v1/orders/{rejected.json()['id']}/cancel")
        assert rejected_cancel.status_code == 409

        missing = client.post("/api/v1/orders/99999/cancel")
        assert missing.status_code == 404

        cancelled_execution = client.post(
            f"/api/v1/executions/orders/{accepted.json()['id']}"
        )
        assert cancelled_execution.status_code == 409
    finally:
        app.dependency_overrides.clear()
