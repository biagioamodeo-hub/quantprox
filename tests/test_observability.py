from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.observability import metrics
from app.core.rate_limit import rate_limiter
from app.main import app


def test_request_ids_security_headers_metrics_and_rate_limits() -> None:
    metrics.reset()
    rate_limiter.reset()
    previous_enabled = settings.rate_limit_enabled
    previous_requests = settings.rate_limit_requests
    previous_window = settings.rate_limit_window_seconds
    client = TestClient(app, headers={"X-API-Key": "dev-api-key"})
    try:
        settings.rate_limit_enabled = True
        settings.rate_limit_requests = 2
        settings.rate_limit_window_seconds = 60

        health = client.get("/health", headers={"X-Request-ID": "trace-123"})
        assert health.status_code == 200
        assert health.headers["x-request-id"] == "trace-123"
        assert health.headers["x-content-type-options"] == "nosniff"
        assert health.headers["x-frame-options"] == "DENY"
        assert health.headers["referrer-policy"] == "no-referrer"

        lab = client.get("/lab/")
        assert lab.status_code == 200
        assert "default-src 'self'" in lab.headers["content-security-policy"]

        first = client.get("/api/v1/metrics")
        second = client.get("/api/v1/metrics")
        limited = client.get("/api/v1/metrics")
        assert first.status_code == second.status_code == 200
        assert "quantprox_http_requests_total" in first.text
        assert first.headers["x-ratelimit-limit"] == "2"
        assert second.headers["x-ratelimit-remaining"] == "0"
        assert limited.status_code == 429
        assert limited.json()["detail"] == "Rate limit exceeded."
        assert int(limited.headers["retry-after"]) > 0
        assert limited.headers["x-request-id"]
    finally:
        settings.rate_limit_enabled = previous_enabled
        settings.rate_limit_requests = previous_requests
        settings.rate_limit_window_seconds = previous_window
        metrics.reset()
        rate_limiter.reset()
