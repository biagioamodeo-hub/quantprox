from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


def test_alpha_decision_to_execution_flow() -> None:
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
            "/api/v1/market-data/instruments", json={"symbol": "ALPHA"}
        ).json()
        portfolio = client.post(
            "/api/v1/portfolios",
            json={"name": "Alpha", "cash_balance": "10000"},
        ).json()
        client.put(
            f"/api/v1/risk/limits/{portfolio['id']}",
            json={
                "max_order_notional": "5000",
                "max_total_exposure": "10000",
            },
        )
        start = datetime(2026, 1, 1, tzinfo=UTC)
        for offset, close in enumerate(("100", "110", "120")):
            client.post(
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

        decision = client.post(
            "/api/v1/decisions/evaluate",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "timeframe": "1d",
                "short_window": 2,
                "long_window": 3,
            },
        ).json()
        assert decision["action"] == "buy"

        order = client.post(
            f"/api/v1/decisions/{decision['id']}/orders",
            json={"quantity": "10", "limit_price": "120"},
        )
        assert order.status_code == 201
        assert order.json()["status"] == "accepted"

        first_fill = client.post(
            f"/api/v1/executions/orders/{order.json()['id']}",
            json={"quantity": "4"},
        )
        assert first_fill.status_code == 201
        assert Decimal(first_fill.json()["notional"]) == Decimal("480")

        partially_filled = client.get(
            "/api/v1/orders", params={"portfolio_id": portfolio["id"]}
        ).json()[0]
        assert partially_filled["status"] == "partially_filled"
        assert Decimal(partially_filled["filled_quantity"]) == Decimal("4")
        assert Decimal(partially_filled["remaining_quantity"]) == Decimal("6")

        excessive_fill = client.post(
            f"/api/v1/executions/orders/{order.json()['id']}",
            json={"quantity": "7"},
        )
        assert excessive_fill.status_code == 422

        execution = client.post(f"/api/v1/executions/orders/{order.json()['id']}")
        assert execution.status_code == 201
        assert Decimal(execution.json()["notional"]) == Decimal("720")

        orders = client.get(
            "/api/v1/orders", params={"portfolio_id": portfolio["id"]}
        ).json()
        assert orders[0]["status"] == "filled"

        positions = client.get(f"/api/v1/portfolios/{portfolio['id']}/positions").json()
        assert Decimal(positions[0]["quantity"]) == Decimal("10")
        assert Decimal(positions[0]["average_price"]) == Decimal("120")

        portfolios = client.get("/api/v1/portfolios").json()
        alpha = next(item for item in portfolios if item["id"] == portfolio["id"])
        assert Decimal(alpha["cash_balance"]) == Decimal("8800")

        executions = client.get(
            "/api/v1/executions", params={"portfolio_id": portfolio["id"]}
        )
        assert executions.status_code == 200
        assert executions.json()[0]["order_id"] == order.json()["id"]
        assert [Decimal(item["quantity"]) for item in executions.json()[:2]] == [
            Decimal("4"),
            Decimal("6"),
        ]

        duplicate = client.post(f"/api/v1/executions/orders/{order.json()['id']}")
        assert duplicate.status_code == 409

        sell_order = client.post(
            "/api/v1/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "sell",
                "quantity": "4",
                "limit_price": "130",
            },
        ).json()
        sell_execution = client.post(f"/api/v1/executions/orders/{sell_order['id']}")
        assert sell_execution.status_code == 201

        positions = client.get(f"/api/v1/portfolios/{portfolio['id']}/positions").json()
        assert Decimal(positions[0]["quantity"]) == Decimal("6")
        assert Decimal(positions[0]["realized_pnl"]) == Decimal("40")
        portfolios = client.get("/api/v1/portfolios").json()
        alpha = next(item for item in portfolios if item["id"] == portfolio["id"])
        assert Decimal(alpha["cash_balance"]) == Decimal("9320")

        oversized_sell = client.post(
            "/api/v1/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "sell",
                "quantity": "10",
                "limit_price": "120",
            },
        ).json()
        insufficient_position = client.post(
            f"/api/v1/executions/orders/{oversized_sell['id']}"
        )
        assert insufficient_position.status_code == 422
        assert (
            insufficient_position.json()["detail"] == "Insufficient position quantity."
        )

        rejected_order = client.post(
            "/api/v1/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "buy",
                "quantity": "100",
                "limit_price": "120",
            },
        ).json()
        assert rejected_order["status"] == "rejected"
        rejected_execution = client.post(
            f"/api/v1/executions/orders/{rejected_order['id']}"
        )
        assert rejected_execution.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_alpha_rejects_invalid_execution_paths() -> None:
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
            "/api/v1/market-data/instruments", json={"symbol": "CASH"}
        ).json()
        portfolio = client.post("/api/v1/portfolios", json={"name": "No cash"}).json()
        client.put(
            f"/api/v1/risk/limits/{portfolio['id']}",
            json={
                "max_order_notional": "1000",
                "max_total_exposure": "1000",
            },
        )
        order = client.post(
            "/api/v1/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "buy",
                "quantity": "1",
                "limit_price": "100",
            },
        ).json()
        no_cash = client.post(f"/api/v1/executions/orders/{order['id']}")
        assert no_cash.status_code == 422
        assert no_cash.json()["detail"] == "Insufficient portfolio cash."

        missing = client.post("/api/v1/executions/orders/99999")
        assert missing.status_code == 404

        hold = client.post(
            "/api/v1/decisions/evaluate",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "timeframe": "1d",
                "short_window": 2,
                "long_window": 3,
            },
        ).json()
        hold_order = client.post(
            f"/api/v1/decisions/{hold['id']}/orders",
            json={"quantity": "1", "limit_price": "100"},
        )
        assert hold_order.status_code == 409

        missing_decision = client.post(
            "/api/v1/decisions/99999/orders",
            json={"quantity": "1", "limit_price": "100"},
        )
        assert missing_decision.status_code == 404

        duplicate_instrument = client.post(
            "/api/v1/market-data/instruments", json={"symbol": "CASH"}
        )
        assert duplicate_instrument.status_code == 409
    finally:
        app.dependency_overrides.clear()
