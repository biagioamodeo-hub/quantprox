from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


def test_order_and_execution_idempotency() -> None:
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
            "/api/v1/market-data/instruments", json={"symbol": "IDEMP"}
        ).json()
        portfolio = client.post(
            "/api/v1/portfolios",
            json={"name": "Idempotent", "cash_balance": "1000"},
        ).json()
        client.put(
            f"/api/v1/risk/limits/{portfolio['id']}",
            json={
                "max_order_notional": "1000",
                "max_total_exposure": "1000",
            },
        )
        order_payload = {
            "portfolio_id": portfolio["id"],
            "instrument_id": instrument["id"],
            "side": "buy",
            "quantity": "2",
            "limit_price": "100",
        }
        headers = {"Idempotency-Key": "order-1"}
        first_order = client.post("/api/v1/orders", json=order_payload, headers=headers)
        replayed_order = client.post(
            "/api/v1/orders", json=order_payload, headers=headers
        )
        assert first_order.status_code == replayed_order.status_code == 201
        assert replayed_order.json()["id"] == first_order.json()["id"]
        assert (
            len(
                client.get(
                    "/api/v1/orders", params={"portfolio_id": portfolio["id"]}
                ).json()
            )
            == 1
        )

        changed_payload = {**order_payload, "quantity": "3"}
        mismatch = client.post("/api/v1/orders", json=changed_payload, headers=headers)
        assert mismatch.status_code == 409
        assert "different payload" in mismatch.json()["detail"]

        execution_headers = {"Idempotency-Key": "execution-1"}
        execution_url = f"/api/v1/executions/orders/{first_order.json()['id']}"
        first_execution = client.post(execution_url, headers=execution_headers)
        replayed_execution = client.post(execution_url, headers=execution_headers)
        assert first_execution.status_code == replayed_execution.status_code == 201
        assert replayed_execution.json()["id"] == first_execution.json()["id"]
        assert Decimal(replayed_execution.json()["notional"]) == Decimal("200")

        current_portfolio = client.get("/api/v1/portfolios").json()[0]
        assert Decimal(current_portfolio["cash_balance"]) == Decimal("800")
        executions = client.get(
            "/api/v1/executions", params={"portfolio_id": portfolio["id"]}
        ).json()
        assert len(executions) == 1

        execution_mismatch = client.post(
            execution_url,
            json={"quantity": "1"},
            headers=execution_headers,
        )
        assert execution_mismatch.status_code == 409
    finally:
        app.dependency_overrides.clear()
