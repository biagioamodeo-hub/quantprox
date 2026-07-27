from hmac import compare_digest

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.config import settings
from app.core.sessions import create_session_token
from app.dependencies.auth import get_current_tenant
from app.schemas.auth import LoginRequest, SessionRead

router = APIRouter()
SESSION_COOKIE = "quantprox_session"


@router.post("/login", response_model=SessionRead)
def login(payload: LoginRequest, response: Response) -> SessionRead:
    expected_password = settings.tenant_api_keys.get(payload.profile)
    if expected_password is None or not compare_digest(
        payload.password, expected_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid profile or password.",
        )
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(payload.profile),
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_secure_cookie,
        samesite="strict",
        path="/",
    )
    return SessionRead(authenticated=True, profile=payload.profile)


@router.get("/session", response_model=SessionRead)
def read_session(tenant_id: str = Depends(get_current_tenant)) -> SessionRead:
    return SessionRead(authenticated=True, profile=tenant_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=settings.session_secure_cookie,
        samesite="strict",
        path="/",
    )
