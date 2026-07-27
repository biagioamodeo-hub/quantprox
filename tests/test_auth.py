from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import app.models
from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


def test_api_requires_a_valid_key_and_isolates_tenants() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)

    def override_session() -> Session:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_session
    previous_keys = settings.tenant_api_keys
    settings.tenant_api_keys = {
        "demo": "dev-api-key",
        "other": "other-api-key",
    }
    anonymous = TestClient(app)
    demo = TestClient(app, headers={"X-API-Key": "dev-api-key"})
    other = TestClient(app, headers={"X-API-Key": "other-api-key"})
    try:
        unauthorized = anonymous.get("/api/v1/portfolios")
        assert unauthorized.status_code == 401
        assert unauthorized.headers["www-authenticate"] == "ApiKey"
        assert (
            anonymous.get(
                "/api/v1/portfolios",
                headers={"X-API-Key": "not-a-real-key"},
            ).status_code
            == 401
        )
        invalid_login = anonymous.post(
            "/auth/login",
            json={"profile": "demo", "password": "wrong-password"},
        )
        assert invalid_login.status_code == 401

        login = anonymous.post(
            "/auth/login",
            json={"profile": "demo", "password": "dev-api-key"},
        )
        assert login.status_code == 200
        assert login.json() == {"authenticated": True, "profile": "demo"}
        assert anonymous.get("/auth/session").json() == login.json()
        assert anonymous.get("/api/v1/portfolios").status_code == 200

        logout = anonymous.post("/auth/logout")
        assert logout.status_code == 204
        assert anonymous.get("/auth/session").status_code == 401

        demo_portfolio = demo.post(
            "/api/v1/portfolios",
            json={"name": "Shared name", "cash_balance": "1000"},
        )
        other_portfolio = other.post(
            "/api/v1/portfolios",
            json={"name": "Shared name", "cash_balance": "2000"},
        )
        assert demo_portfolio.status_code == 201
        assert other_portfolio.status_code == 201
        assert demo.get("/api/v1/portfolios").json() == [demo_portfolio.json()]
        assert other.get("/api/v1/portfolios").json() == [other_portfolio.json()]

        cross_tenant = other.get(
            f"/api/v1/portfolios/{demo_portfolio.json()['id']}/positions"
        )
        assert cross_tenant.status_code == 404
        assert cross_tenant.json()["detail"] == "Portfolio not found."
    finally:
        settings.tenant_api_keys = previous_keys
        app.dependency_overrides.clear()
