from fastapi.testclient import TestClient

from app.main import app


def test_health_check() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_alpha_lab_is_served() -> None:
    client = TestClient(app)

    response = client.get("/lab/")

    assert response.status_code == 200
    assert "QuantProX · Alpha Lab" in response.text
    assert client.get("/lab/app-purchase.js").status_code == 200
