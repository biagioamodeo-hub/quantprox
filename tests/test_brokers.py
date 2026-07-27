from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


def test_sandbox_broker_submission_is_safe_and_tenant_isolated() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    def override_session() -> Session:
        with Session(engine) as session:
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
            "/api/v1/market-data/instruments", json={"symbol": "SANDBOX"}
        ).json()
        portfolio = demo.post(
            "/api/v1/portfolios",
            json={"name": "Sandbox", "cash_balance": "1000"},
        ).json()
        demo.put(
            f"/api/v1/risk/limits/{portfolio['id']}",
            json={
                "max_order_notional": "1000",
                "max_total_exposure": "1000",
            },
        )
        order = demo.post(
            "/api/v1/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "buy",
                "quantity": "2",
                "limit_price": "100",
            },
        ).json()
        url = f"/api/v1/brokers/sandbox/orders/{order['id']}"
        first = demo.post(url)
        replay = demo.post(url)
        assert first.status_code == replay.status_code == 201
        assert replay.json()["id"] == first.json()["id"]
        assert first.json()["provider"] == "sandbox"
        assert first.json()["status"] == "accepted"
        assert other.get(url).status_code == 404

        cancelled = demo.post(f"{url}/cancel")
        assert cancelled.status_code == 200
        assert cancelled.json()["status"] == "cancelled"
        assert demo.get(url).json()["status"] == "cancelled"
        assert demo.post(f"{url}/cancel").status_code == 409
        assert demo.post(f"/api/v1/executions/orders/{order['id']}").status_code == 409
        local_order = demo.get(
            "/api/v1/orders", params={"portfolio_id": portfolio["id"]}
        ).json()[0]
        assert local_order["status"] == "cancelled"

        rejected = demo.post(
            "/api/v1/orders",
            json={
                "portfolio_id": portfolio["id"],
                "instrument_id": instrument["id"],
                "side": "buy",
                "quantity": "20",
                "limit_price": "100",
            },
        ).json()
        rejected_submission = demo.post(
            f"/api/v1/brokers/sandbox/orders/{rejected['id']}"
        )
        assert rejected_submission.status_code == 409
    finally:
        settings.tenant_api_keys = previous_keys
        app.dependency_overrides.clear()


def test_revolut_demo_purchase_never_uses_real_money() -> None:
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})
    response = client.post(
        "/api/v1/brokers/revolut-demo/purchases",
        json={
            "asset_type": "etf",
            "asset_label": "ETF",
            "virtual_balance": "10000",
            "amount": "2500",
            "currency": "EUR",
        },
    )
    assert response.status_code == 201
    receipt = response.json()
    assert receipt["provider"] == "revolut_demo"
    assert receipt["status"] == "completed"
    assert receipt["simulated_fee"] == "6.25"
    assert receipt["total_debit"] == "2506.25"
    assert receipt["remaining_balance"] == "7493.75"
    assert "esclusivamente virtuale" in receipt["disclaimer"]


def test_revolut_demo_rejects_insufficient_virtual_balance() -> None:
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})
    response = client.post(
        "/api/v1/brokers/revolut-demo/purchases",
        json={
            "asset_type": "stock",
            "asset_label": "Azioni",
            "virtual_balance": "1000",
            "amount": "1000",
            "currency": "EUR",
        },
    )
    assert response.status_code == 409


def test_revolut_demo_card_is_linked_without_real_card_data() -> None:
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})
    response = client.post(
        "/api/v1/brokers/revolut-demo/cards",
        json={
            "account_label": "Revolut Demo",
            "virtual_balance": "10000",
            "currency": "EUR",
        },
    )
    assert response.status_code == 201
    card = response.json()
    assert card["linked"] is True
    assert card["network"] == "VISA"
    assert card["masked_number"].startswith("•••• •••• •••• ")
    assert card["spending_limit"] == "10000.00"
    assert "non è una carta Revolut reale" in card["disclaimer"]
