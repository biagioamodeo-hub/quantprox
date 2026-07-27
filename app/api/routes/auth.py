from hmac import compare_digest

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.accounts import create_password_hash, verify_password
from app.core.config import settings
from app.core.sessions import create_session_token
from app.db.session import get_db_session
from app.dependencies.auth import get_current_tenant
from app.models.accounts import UserAccount
from app.schemas.auth import LoginRequest, RegisterRequest, SessionRead

router = APIRouter()
SESSION_COOKIE = "quantprox_session"


@router.post("/login", response_model=SessionRead)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db_session),
) -> SessionRead:
    expected_password = settings.tenant_api_keys.get(payload.profile)
    configured_account = expected_password is not None and compare_digest(
        payload.password, expected_password
    )
    account = db.scalar(
        select(UserAccount).where(
            UserAccount.profile == payload.profile.strip().lower()
        )
    )
    stored_account = account is not None and verify_password(
        payload.password, account.password_hash, account.password_salt
    )
    if not configured_account and not stored_account:
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


@router.post(
    "/register", response_model=SessionRead, status_code=status.HTTP_201_CREATED
)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db_session),
) -> SessionRead:
    normalized_profile = payload.profile.strip().lower()
    existing_account = db.scalar(
        select(UserAccount).where(
            or_(
                UserAccount.profile == normalized_profile,
                UserAccount.email == payload.email.strip().lower(),
            )
        )
    )
    if normalized_profile in settings.tenant_api_keys or existing_account is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists.",
        )
    password_hash, password_salt = create_password_hash(payload.password)
    account = UserAccount(
        profile=normalized_profile,
        full_name=payload.full_name.strip(),
        email=payload.email.strip().lower(),
        phone=payload.phone.strip() if payload.phone else None,
        preferred_currency=payload.preferred_currency,
        password_hash=password_hash,
        password_salt=password_salt,
    )
    db.add(account)
    db.commit()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(account.profile),
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_secure_cookie,
        samesite="strict",
        path="/",
    )
    return SessionRead(authenticated=True, profile=account.profile)


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
