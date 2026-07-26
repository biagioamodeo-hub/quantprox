from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import DomainError

app = FastAPI(
    title=settings.app_name, version=settings.app_version, debug=settings.debug
)
app.include_router(api_router, prefix="/api/v1")
app.mount(
    "/lab",
    StaticFiles(directory=Path(__file__).parent / "static", html=True),
    name="alpha-lab",
)


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
