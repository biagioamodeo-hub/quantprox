from fastapi.testclient import TestClient

from app.main import app


def test_guided_plan_automates_a_cautious_profile() -> None:
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})

    response = client.post(
        "/api/v1/guidance/plan",
        json={
            "starting_capital": "10000",
            "goal": "preservation",
            "horizon_years": 2,
            "maximum_acceptable_loss_percent": "6",
        },
    )

    assert response.status_code == 200
    plan = response.json()
    assert plan["profile"]["code"] == "cautious"
    assert plan["profile"]["allocation_percent"] == "25"
    assert plan["max_order_notional"] == "500.00"
    assert plan["max_total_exposure"] == "2500.00"
    assert plan["backtest"]["trades"] > 0
    assert plan["backtest"]["costs_paid"] != "0.00"
    assert plan["backtest"]["market_scenarios"] == 3
    assert plan["backtest"]["observations"] == 168
    assert 0 <= plan["backtest"]["risk_score"] <= 100
    assert 0 <= plan["backtest"]["confidence_score"] <= 100
    assert "non costituisce consulenza finanziaria" in plan["disclaimer"]


def test_guided_plan_selects_dynamic_only_for_compatible_inputs() -> None:
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})

    response = client.post(
        "/api/v1/guidance/plan",
        json={
            "starting_capital": "25000",
            "goal": "growth",
            "experience": "experienced",
            "horizon_years": 12,
            "maximum_acceptable_loss_percent": "25",
        },
    )

    assert response.status_code == 200
    plan = response.json()
    assert plan["profile"]["code"] == "dynamic"
    assert plan["strategy"]["fee_percent"] == "0.10"
    assert plan["strategy"]["slippage_percent"] == "0.05"


def test_guided_plan_validates_beginner_inputs() -> None:
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})

    response = client.post(
        "/api/v1/guidance/plan",
        json={
            "starting_capital": "100",
            "goal": "balanced",
            "horizon_years": 0,
            "maximum_acceptable_loss_percent": "1",
        },
    )

    assert response.status_code == 422


def test_beginner_plan_never_selects_dynamic_profile() -> None:
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})

    response = client.post(
        "/api/v1/guidance/plan",
        json={
            "starting_capital": "25000",
            "goal": "growth",
            "horizon_years": 20,
            "maximum_acceptable_loss_percent": "30",
        },
    )

    assert response.status_code == 200
    assert response.json()["profile"]["code"] == "balanced"


def test_purchase_safety_accepts_prudent_government_bond_simulation() -> None:
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})
    response = client.post(
        "/api/v1/guidance/purchase-safety",
        json={
            "asset_type": "government_bond",
            "available_capital": "10000",
            "requested_amount": "2500",
            "horizon_years": 5,
            "maximum_acceptable_loss_percent": "8",
            "emergency_fund_available": True,
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["outcome"] == "proceed_simulation"
    assert result["prudent_amount"] == "3000.00"
    assert result["checks_passed"] == result["checks_total"] == 4


def test_purchase_safety_blocks_unsuitable_stock_purchase() -> None:
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})
    response = client.post(
        "/api/v1/guidance/purchase-safety",
        json={
            "asset_type": "stock",
            "available_capital": "10000",
            "requested_amount": "3000",
            "horizon_years": 2,
            "maximum_acceptable_loss_percent": "5",
            "emergency_fund_available": False,
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["outcome"] == "not_suitable"
    assert result["risk_level"] == "elevato"
    assert result["checks_passed"] == 0


def test_purchase_safety_recommends_reducing_excess_amount() -> None:
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})
    response = client.post(
        "/api/v1/guidance/purchase-safety",
        json={
            "asset_type": "bond",
            "available_capital": "10000",
            "requested_amount": "3000",
            "horizon_years": 5,
            "maximum_acceptable_loss_percent": "10",
            "emergency_fund_available": True,
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert result["outcome"] == "reduce_amount"
    assert result["prudent_amount"] == "2000.00"
