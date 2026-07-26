import json
import logging
import re
from collections.abc import Awaitable, Callable
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from starlette.responses import Response

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import DomainError
from app.core.observability import metrics
from app.core.rate_limit import rate_limit_identity, rate_limiter
from app.db.session import engine

logger = logging.getLogger("uvicorn.error.quantprox.access")
logger.setLevel(logging.INFO)
request_id_pattern = re.compile(r"^[A-Za-z0-9._-]{1,128}$")

app = FastAPI(
    title=settings.app_name, version=settings.app_version, debug=settings.debug
)
app.include_router(api_router, prefix="/api/v1")
app.mount(
    "/lab",
    StaticFiles(directory=Path(__file__).parent / "static", html=True),
    name="alpha-lab",
)


@app.middleware("http")
async def observe_and_secure(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    started_at = perf_counter()
    supplied_request_id = request.headers.get("X-Request-ID", "")
    request_id = (
        supplied_request_id
        if request_id_pattern.fullmatch(supplied_request_id)
        else str(uuid4())
    )
    rate_result = None
    response: Response
    if settings.rate_limit_enabled and request.url.path.startswith("/api/v1"):
        identity = rate_limit_identity(
            request.headers.get("X-API-Key"),
            request.client.host if request.client else None,
        )
        rate_result = rate_limiter.check(
            identity,
            settings.rate_limit_requests,
            settings.rate_limit_window_seconds,
        )
        if not rate_result.allowed:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded."},
                headers={"Retry-After": str(rate_result.retry_after)},
            )
        else:
            response = await call_next(request)
    else:
        response = await call_next(request)

    duration = perf_counter() - started_at
    route_object = request.scope.get("route")
    route = getattr(route_object, "path", request.url.path)
    metrics.observe(request.method, route, response.status_code, duration)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/lab"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; connect-src 'self'; "
            "img-src 'self' data:; style-src 'self'; script-src 'self'"
        )
    if rate_result is not None:
        response.headers["X-RateLimit-Limit"] = str(rate_result.limit)
        response.headers["X-RateLimit-Remaining"] = str(rate_result.remaining)
    logger.info(
        json.dumps(
            {
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "route": route,
                "status": response.status_code,
                "duration_ms": round(duration * 1000, 3),
            },
            separators=(",", ":"),
        )
    )
    return response


@app.exception_handler(DomainError)
async def handle_domain_error(request: Request, exception: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exception.status_code, content={"detail": exception.detail}
    )


@app.exception_handler(IntegrityError)
async def handle_integrity_error(
    request: Request, exception: IntegrityError
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "The resource conflicts with existing data."},
    )


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
def readiness_check() -> JSONResponse:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable"},
        )
    return JSONResponse(content={"status": "ready"})
